import psycopg
import re
from sql_conn import SqlConnection
import cdx_toolkit

company_re = re.compile(r"https://job-boards.greenhouse.io/([0-9a-z]+)(/jobs/([0-9]+))?")

def get_company(url):
  url = url.split('?')[0] #remove url params
  match = company_re.match(url)
  if match:
    return match.group(1)
  return ''
  
def download_greenhouse_list(test=False):
  companies = set([])
  cdx = cdx_toolkit.CDXFetcher(source='cc')
  url = f"job-boards.greenhouse.io/*"
  for obj in cdx.iter(url):
    print( obj.data.get('status'), get_company(obj.data.get('url')))
    if '200' <= obj.data.get('status') < '400':
      company = get_company(obj.data.get('url'))
      if company:
        companies.add(company)
  return list(companies)
      
def save_companies(companies):
  with SqlConnection() as cur:
    stale_query = "update companies set stale = 1 where id not in (%s)" % ', '.join('%s' for _ in companies)
    cur.execute(stale_query, tuple(companies))
  for comp in companies:
    try:
      with SqlConnection() as cur:
        cur.execute("INSERT INTO companies values(%s, '', 0)", (comp,))
    except  (psycopg.IntegrityError, psycopg.errors.UniqueViolation):
      pass
    except Exception as e:
      print(e)
    
companies = download_greenhouse_list()
companies = sorted(set(companies))
print (companies)
save_companies(companies)
