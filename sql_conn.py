import re
import os
import psycopg

DB_NAME = os.environ['DATABASE_URL']

class SqlConnection():
  def __enter__(self):
    self.con = psycopg.connect(DB_NAME)
    self.cursor = self.con.cursor()
    return self.cursor
  def __exit__(self, exc_type, exc_val, exc_tb):
    self.con.commit()
    self.cursor.close()
    self.con.close()
