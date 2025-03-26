import sqlite3
from sql_conn import SqliteConnection

def f():
  with SqliteConnection() as s:
    query = "UPDATE jobs SET remote = 1 WHERE location REGEXP 'remote'"
    result = s.execute(query)  
    query = "UPDATE jobs SET remote = 0 WHERE not location REGEXP 'remote'"
    result = s.execute(query)  
    print(result)

def g():
  with SqliteConnection() as s:
    query = "UPDATE jobs SET country = 'US' WHERE location REGEXP '.*\b(US|USA|United States|U.S.|U.S.A.)\b.*'"
    query = "SELECT * FROM jobs WHERE location REGEXP '.*\b(US|USA|United States|U.S.|U.S.A.)\b.*'"
    result = s.execute(query)  
    jobs = result.fetchall()
    print(jobs)





g()

