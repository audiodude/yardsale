import hashlib
import logging
import os
import random
import re
import time

import ebaysdk.finding
import flask
import pylibmc
import yaml

def configure_ebay():
  config = {
    'name': 'ebay_api_config',
    'svcs.ebay.com': {
      'appid': os.environ['EBAY_APP_ID'],
      'version': '1.0.0',
    },
    'open.api.ebay.com': {
      'appid': os.environ['EBAY_APP_ID'],
      'version': 671,
    },
  }
  with open('ebay.yaml', 'w') as f:
    f.write(yaml.dump(config))
configure_ebay()

app = flask.Flask(__name__)

TERMS = (
  "Star Wars", "Leopard Print", "Toaster", "Mug", "Parka", "Harry Potter",
  "Ice Cream", "Lampshade", "Ninja Turtles", "Baby Duck", "Christmas",
  "Strainer", "Penguin", "Shotglass", "The Beatles", "1990s",
  "Aqua", "Floral Print", "Maxi Dress", "Tin Bucket",
  "Picture Frame", "Guitar", "Ginger Ale", "Panda",
  "New York Mets", "Boston Red Sox", "Lightbulbs", "Gummy Bear",
  "Vintage Sweatshirt", "College Shirt", "Sleeping Bag", "Hot Pink",
  "Vase", "Andy Warhol", "Justin Bieber", "Vogue", "Skirt",
  "Teacup", "Dinosaurs", "McDonalds", "Trashcan", "Salt Shaker",
  "Mexico", "Camera", "Snowglobe", "Earmuffs", "Mask", "Hello Kitty",
  "Computer", "Charger", "Typewriter", "Ping Pong", "Magnet", "Paperclip",
  "Ruby", "Board game", "Vodka", "Dollar sign", "Zebra", "Campbell", "Coke",
  "Diamond", "Vase", "Neon green", "Glitter", "Sparkles", "Pearls", "Feather",
  "Hat Pin", "Crown", "Lord of the Rings", "Burger King", "Burrito", "Hello Kitty"
)
NUM_ITEMS = 8
CACHE = pylibmc.Client([os.environ['MEMCACHE_URL']],
                       behaviors={'verify_keys': 1})

TITLE_STOP_WORDS = [
  'of', 'the', 'and', 'is',
  'on', 'at', 'with', 'shop',
  'huge', 'new', 'by', 'as',
  'lot', 'pack', 'pk', 'sz',
  'nib', 'oz', 'in', 'big', 'more',
  'shipping', 'free', 'free shipping', 'size',
  'for', r'\d+gb', r'\d+', 'rare',
  'gift', 'idea', 'ounce', 'nt',
]
STOP_WORDS_PART = '|'.join(TITLE_STOP_WORDS)
STOP_WORD = r'(%s)' % STOP_WORDS_PART
JUNK_CHARS = r'[\(\)\{\}\[\].+=\-~_*&^$\'"#@!/\\]'
REGEX_DIRTY_TITLE = re.compile(
  ' %(stop)s | .. |^%(stop)s|%(stop)s$|\w*%(junkchars)s+\w*|'
  '%(junkchars)s+\w*%(junkchars)s+' % {'stop': STOP_WORD, 'junkchars': JUNK_CHARS},
  re.I)
REGEX_MULTISPACE = re.compile(' +')
REGEX_EDGE_SPACE = re.compile('^ +| +$')
def clean_title(title):
  return REGEX_EDGE_SPACE.sub('', REGEX_MULTISPACE.sub(' ', REGEX_DIRTY_TITLE.sub(' ', title)))

def get_pic(item):
  return item.get('galleryPlusPictureURL') or item.get('galleryURL')

def js_escape(s):
  return s.replace("'", r"\'")

def rep_quote(s):
  return s.replace('"', r'\"')

def fix_casing(words):
  """Turns 'STEEL MAGNOLIA' into 'Steel magnolia'"""
  words[0] = words[0][0].upper() + words[0][1:]
  words[1] = words[1].lower()

@app.route('/')
def index():
  api = ebaysdk.finding.Connection()

  given_term = flask.request.args.get('term')
  if given_term:
    given_term = given_term.lower()
    terms = [given_term]*8
  else:
    terms = set()
    term = None
    while len(terms) < NUM_ITEMS:
      while not term or term in terms:
        term = random.choice(TERMS)
      terms.add(term)

  seen_imgs = set()
  display_items = []
  for term in terms:
    resp = CACHE.get(hashlib.md5(term).hexdigest())
    if not resp:
      response = api.execute('findItemsAdvanced', {
          'keywords': term, 'paginationInput': {'entriesPerPage': 25},
          'affiliate': {'networkId': 9, 'trackingId': '5337405548'},
      })
      resp = response.dict()
      CACHE.set(hashlib.md5(term).hexdigest(), resp, time=180)
    if resp['paginationOutput']['totalEntries'] == '0':
      continue

    resp_item = resp['searchResult']['item']
    if not isinstance(resp_item, list):
      item = resp_item
    else:
      item = None
      pic_to_item = dict((get_pic(item), item) for item in resp_item)
      pics = pic_to_item.keys()
      if len(seen_imgs) >= len(pics):
        continue
      while item is None or item_pic in seen_imgs:
        item_pic = random.choice(pics)
        item = pic_to_item[item_pic]
      seen_imgs.add(item_pic)

    dirty_title = item.get('title')
    title = clean_title(dirty_title)
    title_tokens = title.split(' ')
    if len(title_tokens) >= 3:
      rand_idx = random.randint(0, len(title_tokens) - 3)
      selected_tokens = title_tokens[rand_idx:rand_idx+2]
      fix_casing(selected_tokens)
    else:
      selected_tokens = title_tokens

    display_item = {
      'sdk_item': item,
      'related': js_escape('+'.join(selected_tokens)),
      'term': term,
    }
    display_items.append(display_item)
  return flask.render_template('index.html', display_items=display_items,
                               given_term=given_term)

if __name__ == "__main__":
    app.run(port=8000, debug=True)
