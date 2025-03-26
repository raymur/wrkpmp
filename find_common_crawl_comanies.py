import json
import requests
from requests import get, Response
import re
import time
from sql_conn import SqliteConnection



LAST_CRAWL = '2025-08'

def get_url(current_char = ''):
  search_url = f"job-boards.greenhouse.io/{current_char}*"
  url = f"https://index.commoncrawl.org/CC-MAIN-{LAST_CRAWL}-index?url={search_url}&output=json"
  return url

def get_job_url(job_posting_obj):
  company_re = re.compile(r"https://job-boards.greenhouse.io/([0-9a-z]+)(/jobs/([0-9]+))?")
  try:
    cc_site = json.loads(job_posting_obj)
  except json.JSONDecodeError as e:
    return '' , ''
  cc_url = cc_site.get('url', '')
  cc_url = cc_url.split('?')[0] #remove url params
  match = company_re.match(cc_url)
  if match:
    company = match.group(1)
    job = match.group(3)
    return company, job
  return '', ''
  

def download_greenhouse_list(test=False):
  companies = []
  jobs = []
  # 0-9, a-z
  chars = [chr(x) for x in range(ord('0'), ord('9') + 1)] + [chr(x) for x in range(ord('a'), ord('z') + 1)]
  if test:
    chars = ['e']
  for char in chars: 
    print(f'downloading "{char}" job urls')
    url = get_url(char)
    response: Response = get(url)
    print(f'response:{response.reason}  code: {response.status_code}\n')
    for line in response.text.split('\n'):
      company, job = get_job_url(line)
      if company:
        companies.append(company)
        if job:
          jobs.append(f'{company},{job}')
    #Common Crawl server (NGINX) throttles requests, I think the default is set up to be 10 requests per minute
    # https://docs.nginx.com/nginx-service-mesh/tutorials/ratelimit-walkthrough/
    time.sleep(6) 
  return companies, jobs

#TODO test this function
def save_url_list(urls):
  with open('data/all_greenhouse.txt', 'w') as f:
    f.write('\n'.join(urls)) 

      
def save_companies(companies):
  with SqliteConnection() as cur:
    for comp in companies:
      try:
        cur.execute("INSERT INTO companies values(?, '')", (comp,))
      except Exception as e:
        print(e)
    


companies, jobs = download_greenhouse_list(test=False)
companies = sorted(set(companies))
jobs = sorted(set(jobs))
save_companies(companies)
