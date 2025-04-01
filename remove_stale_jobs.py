from requests import ConnectTimeout, Timeout, TooManyRedirects, get
from sql_conn import SqlConnection

def mark_as_stale(job, company):
  print(f'{company}, {job}: setting stale')
  with SqlConnection() as s:
    q = "UPDATE jobs SET stale = 1 where id = %s AND company_id = %s"
    res = s.execute(q, (job,company))

def has_200_response(job, company):
  gh_url = f"https://job-boards.greenhouse.io/{company}/jobs/{job}"
  try:
    response = get(gh_url, timeout=15,  allow_redirects=False)
  except TooManyRedirects:
    print('error, too many redirects')
    return False
  except (ConnectTimeout, Timeout):
    print('connection timeout')
    return False
  return 200  <= response.status_code < 300
    
with SqlConnection() as s:
  q = "SELECT company_id, id from jobs LIMIT 40000 OFFSET 450"
  res = s.execute(q)
  jobs = res.fetchall()  
for company, job in jobs:
  set_stale = not has_200_response(job, company)
  if set_stale:
    mark_as_stale(job, company)

    
    