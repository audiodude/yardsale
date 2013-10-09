import ebaysdk
import flask
import random
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

@app.route('/')
def index():
  api = ebaysdk.finding()

  if flask.request.args.get('term'):
    terms = [flask.request.args.get('term')]*8
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
          'keywords': term, 'paginationInput': {'entriesPerPage': 25}
      })
      resp = api.response_dict()
      CACHE[term] = {}
      CACHE[term]['resp'] = resp
      CACHE[term]['ttl'] = time.time() + random.randint(350, 450)

    item = random.choice(resp['searchResult']['item'])
    while (item.get('galleryPlusPictureURL', {}).get('value') in seen_imgs or
           item['galleryURL']['value'] in seen_imgs):
      item = random.choice(resp['searchResult']['item'])
    if 'galleryPlusPictureUrl' in item:
      seen_imgs.add(item['galleryPlusPictureURL']['value'])
    seen_imgs.add(item['galleryURL']['value'])

    title_tokens = item['title']['value'].split(' ')
    rand_idx = random.randint(0, len(title_tokens) - 2)
    item['related'] = '+'.join(title_tokens[rand_idx:rand_idx+2])
    item['term'] = term
    items.append(item)
  return flask.render_template('index.html', items=items)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
