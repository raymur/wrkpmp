import re 
from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
import html

salary_re = (
    r'(?:\b[A-Z]{3}\W*|)'
    r'[\$₩€¥£]?[^\w\$₩€¥£]*'
    r'[0-9]{2,3},?[0-9]{3}'
    r'(?:\.[0-9]{2}|)'
     r'(?:\W*[A-Z]{3}\b|)'
     
r'(?:\W*(?:-|–|—|to|and)\W*'
r'(?:[A-Z]{3}|)'
r'\W*[\$₩€¥£]?[^\w\$₩€¥£]*'
r'[0-9]{2,3},?[0-9]{3}'
r'(?:\.[0-9]{2}|)'  
r'(?:\W*[A-Z]{3}\b|)'
r')?'
)

salary_snippit_re = re.compile(
    r'.{0,100}'
    + salary_re +
    r'.{0,100}'
  , re.DOTALL
)

salary_only_re = re.compile(salary_re)

salary_words = set([
  'comp',
  'compensation',
  'pay',
  'salary',
  'tc',
  'wage',
])

class SalaryFinder:
  @staticmethod
  def find_salary(content):
    content = html.unescape(content)
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text()
    return SalaryFinder.find_salary_from_text(text)
  
  @staticmethod
  def find_salary_from_text(text):
    salary_items = []
    money_phrases = salary_snippit_re.findall(text)
    tokenizer = RegexpTokenizer(r'\w+')
    for money_phrase in money_phrases:
      tokens = tokenizer.tokenize(money_phrase)
      final_words = [word.lower() for word in tokens]
      final_words = set(final_words)
      is_likely_salary = len(salary_words.intersection(final_words)) >= 1
      if is_likely_salary:
        salary_item = salary_only_re.search(money_phrase)
        if salary_item:
          salary_items.append(salary_item.group().strip())
    salary_item = list(set(salary_items))
    return '; '.join(salary_items)

