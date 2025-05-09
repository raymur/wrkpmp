import json
import sys
import psycopg
from requests import  TooManyRedirects, get
from requests.exceptions import ConnectTimeout , Timeout, SSLError, ConnectionError
from bs4 import BeautifulSoup
import re 
from salary_finder import SalaryFinder
from sql_conn import SqlConnection

import logging

#TODO create logger class
logger = logging.getLogger(__name__)


job_json_re = re.compile(r"window.__remixContext = (.*);")  #possible bug here
job_in_html_re = re.compile(r'\bjobs/[0-9]{5,}\b')

us_states = r"Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY"
us_states_re = re.compile(r'\b(' + us_states + r')\b')
us = r'\b(US|USA|United States|U.S.|U.S.A.)\b'
us_re = re.compile(us)

def listify(l):
  return '(' + ','.join([f"'{x}'" for x in l]) + ')'

def is_in_us(location):
  return us_re.search(location) or us_states_re.search(location)

def is_remote(location):
  return 'remote' in location.lower()

def execute_command(command, data=(), res_fn=lambda x: None):
  with SqlConnection() as cur: 
    try:
      res = cur.execute(command, data)
      res_fn(res)
    except psycopg.ProgrammingError:
      logger.error(command, data,)

def update_company_name(company, company_name):
  with SqlConnection() as cur:
    cur.execute(" update companies set name=%s where id=%s", (company_name, company))


def update_stale_jobs(current_job_ids, company):
  query = "update jobs set stale=1 where company_id=%s"
  if current_job_ids:
    placeholder_list = ','.join('%s' for _ in current_job_ids)
    query +=  f" AND id NOT IN ({placeholder_list})"
  parameters = ((company,) + tuple(current_job_ids))
  with SqlConnection() as cur:
    cur.execute(query, parameters)
  

def save_job(job_id, company, title, location, published, salary):
  remote = 1 if is_remote(location) else 0
  country = 'US' if is_in_us(location) else ''
  stale = 0
  try: 
    with SqlConnection() as cur:
      cur.execute("INSERT INTO jobs values(%s, %s, %s, %s, %s, %s, %s, %s, %s)", (job_id, title, location, company, remote, country, stale, published, salary))
    return job_id
  except (psycopg.IntegrityError, psycopg.errors.UniqueViolation):
    with SqlConnection() as cur:
      cur.execute(" update jobs set title=%s, location=%s, company_id=%s, remote=%s, country=%s, published=%s, salary=%s where id=%s", (title, location, company, remote, country, published, salary, str(job_id)))

def log_job_count():
  execute_command('SELECT count(*) from jobs', res_fn=lambda res: logger.info(f"total jobs: {res.fetchall()[0][0]}"))

def do_ugly_parsing(script):
  decoded_script = script.decode_contents()
  match =  job_json_re.match(decoded_script)
  if not match or not match.group(1):
    return [], '', 1, 1
  job_json = match.group(1)
  job_dict = json.loads(job_json)
  obj = job_dict\
      .get("state")\
      .get("loaderData")\
      .get("routes/$url_token")    ##possible bug here, key not always right
  company_name = obj.get("board", {}).get('name' ,'')
  job_posts = obj.get("jobPosts")
  job_data = job_posts.get("data")
  
  
  total_pages = job_posts.get("total_pages")
  page = job_posts.get("page")
  return job_data, company_name, total_pages, page

def get_job_attributes(job):
  content = job.get('content' or '')
  salary = SalaryFinder.find_salary(content)
  job_id = str(job.get('id'))
  title = job.get('title') or ''
  location = job.get('location') or ''
  published = job.get('published_at') or ''
  return job_id, title, location, published, salary

def get_company_response(company, page):
  gh_url = f"https://job-boards.greenhouse.io/{company}?page={page}"
  try:
    response = get(gh_url, timeout=10, )
    return response.text, response.status_code
  except TooManyRedirects:
    logger.error(company + ': error, too many redirects')
  except (ConnectTimeout, Timeout):
    logger.error(company + ': connection timeout')
  except SSLError:
    logger.error(company + ': ssl error')
  except ConnectionError:
    logger.error(company + ': connection error')
  except Exception as e:
    logger.error(company + ': Unhandled exception')
    logger.error(e)
  return None, None

# returns list of new jobs saved
def lookup_jobs(company, page=1):
  job_ids = []
  html, status_code = get_company_response(company, page)
  if not html:
    return []
  if status_code < 200 or status_code > 300:
    logger.warning (f'{company}: {status_code}')
    update_stale_jobs([], company)
    return []
  logger.info(f'{company}: {status_code}')
  soup = BeautifulSoup(html, 'html.parser')
  scripts = soup.find_all('script')
  for script in scripts:
    job_data, company_name, total_pages, page = do_ugly_parsing(script)
    if not job_data:
      continue
    for job in job_data:
      job_id, title, location, published, salary = get_job_attributes(job)
      save_job(job_id, company, title, location, published, salary)
      job_ids.append(job_id)
    if total_pages > page:
      return job_ids + lookup_jobs(company, page + 1) #recurse
    if company_name:
      update_company_name(company, company_name)
  return job_ids
  # possible_jobs = job_in_html_re.findall(html) # this can be used to get jobs another way if not found in the script


def load_companies(first_company=''):
  with SqlConnection() as s:
    query =  "SELECT id FROM companies where id >= %s AND stale = 0 order by id"
    res = s.execute(query, (first_company,)) 
    return [company for (company,) in res.fetchall()]

def get_first_company():
  try:
    return sys.argv[1]
  except (IndexError, TypeError, ValueError):
    return ''

if __name__ == '__main__':
  logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
  new_job_count = 0
  first_company_option = get_first_company()
  companies = load_companies(first_company_option)
  interval = len(companies)//10 if len(companies) >= 10 else 1
  for i, company in enumerate(companies, 1):
    current_job_ids = lookup_jobs(company)
    update_stale_jobs(current_job_ids, company)
    new_job_count += len(current_job_ids)
    if i % interval == 0:
      progress_percent = i*100/len(companies)
      logger.info(f'{progress_percent}% complete')      
  logger.info(f"added {new_job_count} new jobs")
  total_job_count = log_job_count()
