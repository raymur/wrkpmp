import json
import sys
from requests import  TooManyRedirects, get
from requests.exceptions import ConnectTimeout , Timeout, SSLError
from bs4 import BeautifulSoup
import re 
import sqlite3
from sql_conn import SqliteConnection


job_json_re = re.compile(r"window.__remixContext = (.*);")
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
  with SqliteConnection() as cur: 
    try:
      res = cur.execute(command, data)
      res_fn(res)
    except sqlite3.ProgrammingError:
      print(command, data,)


def update_stale_jobs(current_job_ids, company):
  with SqliteConnection() as cur:
    query = " update jobs set stale=1 where company_id==? AND id NOT IN (%s)" % ','.join('?' for _ in current_job_ids)
    parameters = ((company,) + tuple(current_job_ids))
    cur.execute(query, parameters)
  

def save_job(job_id, company, title, location, published):
  remote = 1 if is_remote(location) else 0
  country = 'US' if is_in_us(location) else ''
  stale = 0
  with SqliteConnection() as cur:
    try: 
      cur.execute("INSERT INTO jobs values(?, ?, ?, ?, ?, ?, ?, ?)", (job_id, title, location, company, remote, country, stale, published))
      return job_id
    except sqlite3.IntegrityError:
      cur.execute(" update jobs set title=?, location=?, company_id=?, remote=?, country=?, published=? where id==?", (title, location, company, remote, country, published, job_id))
      

def print_jobs():
  execute_command('SELECT * from jobs', res_fn=lambda res: print(res.fetchall()))

def print_job_count():
  execute_command('SELECT count(*) from jobs', res_fn=lambda res: print(f"total jobs: {res.fetchall()[0][0]}"))

# returns list of new jobs saved
def lookup_jobs(company, page=1):
  job_ids = []
  gh_url = f"https://job-boards.greenhouse.io/{company}?page={page}"
  try:
    response = get(gh_url, timeout=15, )
  except TooManyRedirects:
    print('error, too many redirects')
    return []
  except (ConnectTimeout, Timeout):
    print('connection timeout')
    return []
  except SSLError:
    print('ssl error')
    return []
  html = response.text
  if 200 <= response.status_code < 300:
    soup = BeautifulSoup(html, 'html.parser')
    for script in soup.find_all('script'):
      match =  job_json_re.match(script.decode_contents())
      if match and match.group(1):
        job_json = match.group(1)
        job_dict = json.loads(job_json)
        job_posts = job_dict\
            .get("state")\
            .get("loaderData")\
            .get("routes/$url_token")\
            .get("jobPosts")
        job_data = job_posts.get("data")
        total_pages = job_posts.get("total_pages")
        page = job_posts.get("page")
        for job in job_data:
          job_id = job.get('id')
          title = job.get('title') or ''
          location = job.get('location') or ''
          published = job.get('published_at') or ''
          save_job(job_id, company, title, location, published)
          job_ids.append(job_id)
        if total_pages > page:
          return job_ids + lookup_jobs(company, page + 1)
        return job_ids
    else: # end for
      # print(html)
      possible_jobs = job_in_html_re.findall((html))
      print (possible_jobs)
      # todo: search html for r'href=\".*/jobs/[0-9]+\"'
  # Possibly 
  print (f'{company}: {response.status_code}')
  update_stale_jobs([], company)
  return [] 

def load_companies(offset=0):
  new_job_count = 0
  with SqliteConnection() as s:
    res = s.execute("SELECT * FROM companies WHERE ROWID >= ?", (offset,)) 
    company_rows = res.fetchall()
  for company, name in company_rows:
    company = company.strip()
    current_job_ids = lookup_jobs(company)
    update_stale_jobs(current_job_ids, company)
    new_job_count += len(current_job_ids)
  return new_job_count

def get_offset():
  try:
    return sys.argv[1]
  except (IndexError, TypeError, ValueError):
    return 0
    

offset = get_offset()
new_job_count = load_companies(offset)
print(f"added {new_job_count} new jobs")
total_job_count = print_job_count()
      
      
