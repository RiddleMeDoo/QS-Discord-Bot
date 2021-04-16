from discord.ext import tasks, commands
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
import aiohttp
from datetime import datetime
from replit import db
from tile import Tile
from exploration import Exploration

class QueslarBot(commands.Bot):
  '''
  This class contains all methods needed for commands
  + loop updates
  '''
  def __init__(self,  *args, **kwargs):
    super().__init__(*args, **kwargs)
    if "channelId" not in db:
      db["channelId"] = os.environ['NOTIFY_CHANNEL']
    
    self.notificationChannel = None #Initialized in setup_loop
    self.tagId = os.environ['TAG']

    self.tiles = [Tile(t) for t in db.get("tiles", [])]
    self.mystery = db.get("mystery","???")
    
    self.exploration = Exploration(db.get("exploration_timer","2000-01-01T00:00:00.000Z"))
    self.scheduler = AsyncIOScheduler({'apscheduler.timezone': 'UTC'})

    self.update_info.start()
    self.scheduler.start()
  

  async def alert_exploration(self):
    '''
    Sends a message to the notification channel when
    the exploration finishes.
    '''
    print("Alert: Exploration done.".format(self.tagId))
    await self.notificationChannel.send("<@&{}> Exploration done!".format(self.tagId))


  async def alert_test(self):
    '''
    Debugging method for sending test message
    '''
    print("Alert test")
    await self.notificationChannel.send("Test alert @here")
  

  @tasks.loop(minutes=5)
  async def update_info(self):
    '''
    Updates the database from the API server, sends messages if
    tiles change, and starts a timer for kd explorations if one 
    is running.
    '''
    #print("{}> Updating info".format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
    success = False

    #Update to database
    data = await self.get_qs_data()
    if(data):
      try:
        #Update only if anything changed
        await self.update_tile_status(data["kingdom"]["tiles"])
        if "mapMisc" in data["kingdom"] and self.mystery != data["kingdom"]["mapMisc"]["mystery_tile"]:
          self.mystery = data["kingdom"]["mapMisc"]["mystery_tile"]
          db["mystery"] = self.mystery

        dataExplo = Exploration(data["kingdom"]["activeExploration"]["exploration_timer"])
        if self.exploration != dataExplo:
          db["exploration_timer"] = data["kingdom"]["activeExploration"]["exploration_timer"]
          self.exploration = dataExplo

        db["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        success = True
      except KeyError as e:
        print("Failed to index {} in API data".format(str(e)))
    else:  
      print("{}> Failed to get API data".format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    # Start exploration timer if there isn't one
    if len(self.scheduler.get_jobs()) == 0 and not self.exploration.is_done():
      end = self.exploration.get_end_time()
      self.scheduler.add_job(self.alert_exploration, "date", run_date=end, id='exploration')
      #self.scheduler.add_job(self.alert_test, "interval", minutes=1, id='exploration') #Debugging alerts
      print("Starting alert for {} UTC...".format(end))
    
    return success


  @update_info.before_loop
  async def setup_loop(self):
    await self.wait_until_ready()
    #Initialize channel
    self.notificationChannel = self.get_channel(db["channelId"])
    if(not self.notificationChannel):
      print("Failed to find channel.")


  async def get_qs_data(self):
    '''
    Returns player data from the API server
    '''
    async with aiohttp.ClientSession() as session:
      async with session.get('https://queslar.com/api/player/full/'+os.environ['QS_KEY']) as res:
        if res.status == 200:
          return await res.json()
        else:
          print("Server error: {}".format(res.status))
          return {}


  async def update_tile_status(self, tiles):
    '''
    Sends a message to the notification channel if 
    tiles have changed since the last update.
    It uses newTiles and the current (old) tiles for
    comparison.
    '''
    i, j = 0, 0
    lost, gained = [], []
    oldTiles = self.tiles
    newTiles = [Tile(t) for t in tiles]
    # Iterate through the tiles and compare changes
    while i < len(oldTiles) and j < len(newTiles):
      if oldTiles[i].id == newTiles[j].id:
        i += 1
        j += 1
      elif oldTiles[i].id < newTiles[j].id:
        lost.append((oldTiles[i].get_coords(), str(oldTiles[i])))
        i += 1
      else:
        gained.append((newTiles[j].get_coords(), str(newTiles[j])))
        j += 1
    if len(oldTiles) < len(newTiles):
      gained += [(tile.get_coords(), str(tile)) for tile in newTiles[j:]]
    elif len(oldTiles) > len(newTiles):
      lost += [(tile.get_coords(), str(tile)) for tile in oldTiles[i:]]
    
    #Send result to channel
    if len(gained) != 0 or len(lost) != 0:
      await self.post_tile_update(gained, lost)
      self.tiles = newTiles
      db["tiles"] = tiles #Update db if anything changed


  def set_notification_channel(self, channel):
    '''
    Sets the notification channel to the given channel.
    '''
    db["channelId"] = channel.id
    self.notificationChannel = channel


  def get_tiles(self):
    '''
    Returns an embed featuring all tiles held by the kd
    '''
    embed = discord.Embed(title="Kingdom Tiles", color=0x0080c0)
    for tile in self.tiles:
      embed.add_field(name=tile.get_coords(), value=str(tile), inline=True)
    embed.set_footer(text="Last updated: {} UTC".format(db["last_updated"]))
    return embed


  async def post_tile_update(self, gained, lost):
    '''
    Sends an embed message to the notification channel if 
    any tiles were lost or gained since the last update. 
    ''' 
    if len(gained) == 0 and len(lost) == 0:
      return
    
    if len(gained) != 0:
      gainedMsg = discord.Embed(title="Tile(s) Gained:", color=0x00ff00)
      for coords, boostType in gained:
        gainedMsg.add_field(name=coords, value=boostType, inline=False)
      await self.notificationChannel.send(embed=gainedMsg)

    if len(lost) != 0:
      lostMsg = discord.Embed(title="Tile(s) Lost:", color=0xce0000)
      for coords, boostType in lost:
        lostMsg.add_field(name=coords, value=boostType, inline=False)
      await self.notificationChannel.send("@here", embed=lostMsg)

  async def stop_timer(self):
    self.scheduler.pause()
    self.scheduler.remove_job("exploration")

  async def restart_timer(self):
    self.scheduler.resume()
    await self.update_info()

  def get_exploration_timer(self):
    if len(self.scheduler.get_jobs()) == 0:
      return "The timer has stopped."

    return str(self.exploration)
  