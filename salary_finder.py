import re 
from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer
import html

salary_snippit_re = re.compile(
    r'.{0,150}'
    r'\W*[$₩€¥£]?\W*[0-9]{2,3},?[0-9]{3}'                    
    r'(?:\W*(?:-|–|—|to)\W*[$₩€¥£][0-9]{2,3},?[0-9]{3})?'
    r'.{0,150}'
)

salary_only_re = re.compile(
    r'[$₩€¥£]?\W*[0-9]{2,3},?[0-9]{3}'                    
    r'(?:\W*(?:-|–|—|to)\W*[$₩€¥£][0-9]{2,3},?[0-9]{3})?'
)

salary_words = set([
  'base',
  'comp',
  'compensation',
  'eur'
  'gbp'
  'pay',
  'salary',
  'tc',
  'usd'
  'wage'
])

class SalaryFinder:
  @staticmethod
  def find_salary(content):
    salary_items = []
    content = html.unescape(content)
    soup = BeautifulSoup(content, 'html.parser')
    text = soup.get_text()
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
    return '; '.join(salary_items)
