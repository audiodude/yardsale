import ebaysdk
import flask
import random
import re
import time

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
  "Hat Pin", "Crown", "Lord of the Rings", "Burger King", "Burrito",
)
NUM_ITEMS = 8
CACHE = {}

TITLE_STOP_WORDS = [
  'of', 'the', 'and', 'is',
  'on', 'at', 'with',
  'huge', 'new', 'by', 'as',
  'lot', 'pack', 'pk',
  'nib', 'oz', 'in', 'big', 'more',
]
STOP_WORDS_PART = '|'.join(TITLE_STOP_WORDS)

REGEX_DIRTY_TITLE = re.compile(
  r'(%s|\d+%%?|[+=-_*&^$#@]) ?' % STOP_WORDS_PART, re.I)

def clean_title(title):
  return REGEX_DIRTY_TITLE.sub('', title)

def get_pic(item):
  return (item.get('galleryPlusPictureURL', {}).get('value') or
          item['galleryURL']['value'])

@app.route('/')
def index():
  api = ebaysdk.finding()

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
  items = []
  for term in terms:
    if term in CACHE and CACHE[term]['ttl'] - time.time() >= 0:
      print 'cached response for %s' % term
      resp = CACHE[term]['resp']
    else:
      print 'fresh response for %s' % term
      api.execute('findItemsAdvanced', {
          'keywords': term, 'paginationInput': {'entriesPerPage': 25},
          'affiliate': {'networkId': 9, 'trackingId': '5337405548'},
      })
      resp = api.response_dict()
      CACHE[term] = {}
      CACHE[term]['resp'] = resp
      CACHE[term]['ttl'] = time.time() + 179
    if resp['searchResult']['count']['value'] == '0':
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

    title = clean_title(item['title']['value'])
    title_tokens = title.split(' ')
    if len(title_tokens) >= 3:
      rand_idx = random.randint(0, len(title_tokens) - 2)
      item['related'] = '+'.join(title_tokens[rand_idx:rand_idx+2])
    else:
      item['related'] = '+'.join(title_tokens)
    item['term'] = term
    items.append(item)
  return flask.render_template('index.html', items=items, given_term=given_term)

if __name__ == "__main__":
    app.run(debug=True)
