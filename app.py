import ebaysdk
import flask
import random
import time

app = flask.Flask(__name__)

TERMS = (
  "Star Wars", "Leopard Print", "Toaster", "Mug", "Parka", "Harry Potter",
  "Ice Cream", "Lampshade", "Ninja Turtles", "Baby Duck", "Christmas",
  "Strainer", "Lemon", "Penguin", "Shotglass", "The Beatles", "1990s",
  "Lipstick", "Aqua", "Floral Print", "Maxi Dress", "Tin Bucket",
  "Picture Frame", "Photo", "Guitar", "Ginger Ale", "Panda",
  "New York Mets", "Boston Red Sox", "Lightbulbs", "Gummy Bear",
  "Vintage Sweatshirt", "College Shirt", "Sleeping Bag", "Hot Pink",
  "Ford", "Vase", "Andy Warhol", "Justin Bieber", "Vogue", "Skirt",
  "Teacup", "Dinosaurs", "McDonalds", "Trashcan", "Salt Shaker", "Beads",
  "Mexico", "Camera", "Snowglobe", "Earmuffs", "Mask", "Hello Kitty",
  "Computer", "Charger", "Typewriter", "Ping Pong", "Magnet", "Paperclip",
  "Ruby", "Board game", "Vodka", "Skunk", "Carrot", "Dollar sign",
)
NUM_ITEMS = 8
CACHE = {}

@app.route('/')
def index():
  api = ebaysdk.finding()

  terms = set()
  term = None
  while len(terms) < NUM_ITEMS:
    while not term or term in terms:
      term = random.choice(TERMS)
    terms.add(term)

  items = []
  for term in terms:
    if term in CACHE and CACHE[term]['ttl'] - time.time() >= 0:
      print 'cached response for %s' % term
      resp = CACHE[term]['resp']
    else:
      print 'fresh response for %s' % term
      api.execute('findItemsAdvanced', {
          'keywords': term, 'paginationInput': {'entriesPerPage': 20}
      })
      resp = api.response_dict()
      CACHE[term] = {}
      CACHE[term]['resp'] = resp
      CACHE[term]['ttl'] = time.time() + random.randint(350, 450)
    items.append(random.choice(resp['searchResult']['item']))
  return flask.render_template('index.html', items=items)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
