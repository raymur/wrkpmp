import sqlite3
from sql_conn import SqliteConnection

IMPORT_FILENAME = 'data/companies.csv'

def add_company(company):
  with SqliteConnection() as s:
    try:
      s.execute("INSERT INTO companies values(?, ?)", (company, ''))
    except sqlite3.IntegrityError:
      pass

def add_companies_from_csv():
  with open(IMPORT_FILENAME, 'r') as f:
    for company in f.read().split('\n'):
      add_company(company)


add_companies_from_csv()