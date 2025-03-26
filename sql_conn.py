import sqlite3
import re
import traceback

DB_NAME = "db/wrkpmp.db"

def regexp(x,y): 
  return 1 if re.search(x,(y or '').lower(), re.IGNORECASE) else 0

def regexpc(x,y): 
  return 1 if re.search(x, y or '') else 0
    
    
# regexp = lambda x, y: 1 if re.search(x,y) else 0

class SqliteConnection():
  def __enter__(self):
    self.con = sqlite3.connect(DB_NAME)
    sqlite3.enable_callback_tracebacks(True)   # <-- !
    self.con.create_function('regexp', 2, regexp)
    self.con.create_function('regexpc', 2, regexpc)
    return self.con.cursor()
  def __exit__(self, exc_type, exc_val, exc_tb):
    self.con.commit()
    self.con.close()
