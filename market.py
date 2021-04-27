from replit import db
import aiohttp
import os
from datetime import datetime

class Market:
  def __init__(self):
    if "prices" in db:
      self.prices = db["prices"]
    else:
      self.prices = {
        "meat" : -1,
        "iron" : -1,
        "wood" : -1,
        "stone" : -1,
        "relics" : -1
      }


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
      if item["market_type"] == "buy" and newPrice:
        self.prices[currency] = newPrice
    

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
    diff = datetime.strptime(db["market_last_updated"], "%Y-%m-%dT%H:%M:%S.000Z") - datetime.utcnow()
    minutes = (diff.seconds % 3600) // 60
    return minutes > 60

