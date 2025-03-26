import json
from requests import  TooManyRedirects, get
from requests.exceptions import ConnectTimeout , Timeout
from bs4 import BeautifulSoup
import re 
import sqlite3
from sql_conn import SqliteConnection


job_json_re = re.compile(r"window.__remixContext = (.*);")




def execute_command(command, data=(), res_fn=lambda x: None):
  with SqliteConnection() as cur: 
    try:
      res = cur.execute(command, data)
      res_fn(res)
    except sqlite3.ProgrammingError:
      print(command, data,)

def save_job(job_id, company, title, location):
  with SqliteConnection() as cur:
    try: 
      cur.execute("INSERT INTO jobs values(?, ?, ?, ?)", (job_id, title, location, company))
      return job_id
    except sqlite3.IntegrityError:
      cur.execute(" update jobs set title=?, location=?, company_id=? where id==?", (title, location, company, job_id))
      

def print_jobs():
  execute_command('SELECT * from jobs', res_fn=lambda res: print(res.fetchall()))

def print_job_count():
  execute_command('SELECT count(*) from jobs', res_fn=lambda res: print(f"total jobs: {res.fetchall()[0][0]}"))

def load_companies():
  # TODO: load companies from DB instead
  # TODO: renae files
  new_job_count = 0
  with SqliteConnection() as s:
    res = s.execute("SELECT * FROM companies limit 10000 offset 213") # TODO : remove offset, just for testing purposes
    company_rows = res.fetchall()
  for company, name in company_rows:
    company = company.strip()
    gh_url = f"https://job-boards.greenhouse.io/{company}"
    print(gh_url)
    try:
      response = get(gh_url, timeout=15)
    except TooManyRedirects:
      print('error, too many redirects')
      continue
    except (ConnectTimeout, Timeout):
      print('connection timeout')
      continue
    html = response.text
    if 200 <= response.status_code < 300:
      soup = BeautifulSoup(html, 'html.parser')
      for script in soup.find_all('script'):
        match =  job_json_re.match(script.decode_contents())
        if match and match.group(1):
          job_json = match.group(1)
          job_dict = json.loads(job_json)
          job_data = job_dict\
              .get("state")\
              .get("loaderData")\
              .get("routes/$url_token")\
              .get("jobPosts")\
              .get("data")
          for job in job_data:
            job_id = job.get('id')
            title = job.get('title')
            location = job.get('location')
            added_job = save_job(job_id, company, title, location)
            new_job_count += 1 if added_job else 0 
    else:
      print (response.status_code)
  return new_job_count

new_job_count = load_companies()
print(f"added {new_job_count} new jobs")
total_job_count = print_job_count()
      
      