
import sys
import json
import re 
from bs4 import BeautifulSoup 
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tokenize import RegexpTokenizer

#NLP libraries
#- NLTK - og library
#- TextBlob - built on NLTK
#- Stanza - competitor of NLTK

s='https://job-boards.greenhouse.io/recidiviz/jobs/4564266006'


words_no_one_cares_about = ['company', 'work', 'team', 'improve', 'experience', 'impact', 'best', 'new', 'looking', 'compensation', 'working', 'ways', 'right', 'processes', 'people', 'make', 'know', 'industry', 'care', 'believe', 'skills', 'project', 'always', 'hiring', 'much', 'enough', 'way', 'want']
words_no_one_cares_about.sort()




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

def get_salary(content):
  salary_items = []
  money_phrases = salary_snippit_re.findall(content)
  print(money_phrases)
  tokenizer = RegexpTokenizer(r'\w+')
  for money_phrase in money_phrases:
    tokens = tokenizer.tokenize(money_phrase)
    final_words = [word.lower() for word in tokens]
    print(final_words)
    final_words = set(final_words)
    is_likely_salary = len(salary_words.intersection(final_words)) >= 1
    if is_likely_salary:
      salary_item = salary_only_re.search(money_phrase)
      if salary_item:
        salary_items.append(salary_item.group().strip())
  return '; '.join(salary_items)

def get_keywords(content):
  d = {}
  sw=stopwords.words('english')
  sw += words_no_one_cares_about
  sw.sort()
  
  soup = BeautifulSoup(content, 'html.parser')
  text = soup.get_text()
  
  tokenizer = RegexpTokenizer(r'\w+')
  tokens = tokenizer.tokenize(text)
  # tokens = word_tokenize(text)
  
  is_stop = lambda w: w.lower() not in sw
  
  
  
  final_words = [word.lower() for word in tokens if is_stop(word)]
  final_words.sort()
  for w in final_words:
    d.setdefault(w, 0)
    d[w] += 1
  # print(d)
  vals = set(d.values())
  dummy_words = []
  vals = [10, 9, 8, 7, 6, 5, 4, 3, 2
          
          ]
  for val in list(vals):
    for k in d:
      if d[k] == val:
        print(d[k] , k)
  print(len(d))
  
  

with open('example_job_posting.json', 'r') as f:
  j = json.load(f)
  
loader_data = j.get("state").get("loaderData")
keys = filter(lambda x: x.startswith('routes/'), loader_data.keys())

for key in keys: 
  content: str = loader_data.get(key).get('jobPost').get('content')
  result = get_salary(content)
  print(result)
  # get_keywords(content)
  
  
  
  
# import nltk
# from nltk import word_tokenize, pos_tag, ne_chunk
# from nltk.tree import Tree
# from nltk.chunk import tree2conlltags

# # # Ensure necessary resources are downloaded
# # nltk.download('punkt_tab')
# # nltk.download('punkt')
# # nltk.download('averaged_perceptron_tagger')
# # nltk.download('maxent_ne_chunker')
# # nltk.download('words')

# def extract_money_entities(text):
#     tokens = word_tokenize(text)
#     pos_tags = pos_tag(tokens)
#     chunked = ne_chunk(pos_tags)
#     print(chunked)
#     iob_tags = tree2conlltags(chunked)
#     print (iob_tags)
#     money_entities = []
#     for subtree in chunked:
#         if isinstance(subtree, Tree) and subtree.label() == 'MONEY':
#             entity = " ".join(token for token, pos in subtree.leaves())
#             money_entities.append(entity)

#     return money_entities

# # Example usage
# text = "Google donated $1,000,000 to UNICEF."
# money_values = extract_money_entities(text)
# print("Extracted currency values:", money_values)