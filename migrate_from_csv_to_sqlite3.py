import psycopg
from sql_conn import SqlConnection

IMPORT_FILENAME = 'data/companies.csv'

def add_company(company):
  with SqlConnection() as s:
    try:
      s.execute("INSERT INTO companies values(%s, %s)", (company, ''))
    except psycopg.IntegrityError:
      pass

def add_companies_from_csv():
  with open(IMPORT_FILENAME, 'r') as f:
    for company in f.read().split('\n'):
      add_company(company)


add_companies_from_csv()