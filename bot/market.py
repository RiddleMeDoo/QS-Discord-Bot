import json
import aiohttp
import os
from datetime import datetime

class Market:
  def __init__(self):
    with open("db.txt","r") as f: #Not the best way of accessing data
      db = json.load(f)
    self.prices = db.get("prices", { 
        "meat" : "-1.0", # Must be str to get around db type restrictions
        "iron" : "-1.0",
        "wood" : "-1.0",
        "stone" : "-1.0",
        "relics" : "-1.0"
      }) 


  async def update(self):
    '''
    Updates prices to the latest snapshot from the server
    Returns True if update was successful
    '''
    newPrices = await self.get_qs_prices()
    if not newPrices: return False

    for item in newPrices:
      currency = item["currency_type"]
      newPrice = self.prices.get(currency, 0)
      #Only update if it's one of the 5 types in self.prices
      if item["market_type"] == "buy" and newPrice:
        self.prices[currency] = str(item["price"])
    

    db["prices"] = self.prices
    db["market_last_updated"] = newPrices[0]["sent_time"]
    return True


  async def get_qs_prices(self):
    '''
    Returns prices from the server
    '''
    async with aiohttp.ClientSession() as session:
      async with session.get('https://queslar.com/api/market/history-latest/'+os.environ['QS_KEY']) as res:
        if res.status == 200:
          return await res.json()

        else:
          print("Server error: {}".format(res.status))
          return []


  def is_outdated(self):
    '''
    Returns True if the most recent timestamp occured more 
    than 1 hour ago.
    '''
    diff =  datetime.utcnow() - datetime.strptime(db.get("market_last_updated", "2000-01-01T00:00:00.000Z"), "%Y-%m-%dT%H:%M:%S.000Z")
    minutes = diff.seconds / 60
    return minutes > 60


  def price_to_str(self, price):
    '''
    Return a truncated str version of the price
    '''
    if price // 1000000000 > 0: #billion
      trunc = str(price / 1000000000)
      return trunc[:trunc.find(".")+3] + "b"
    elif price // 1000000 > 0: #million
      trunc = str(price / 1000000)
      return trunc[:trunc.find(".")+3] + "m"
    elif price // 100000 > 0: #hundred thousand
      trunc = str(price / 100000)
      return trunc[:trunc.find(".")+3] + "k"
    else:
      trunc = str(price/1)
      return trunc[:trunc.find(".")+3]
