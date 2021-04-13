from discord.ext import tasks, commands
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
import aiohttp
from datetime import datetime
from replit import db

class QueslarBot(commands.Bot):
  '''
  This class contains all methods needed for commands
  + loop updates
  '''
  def __init__(self,  *args, **kwargs):
    super().__init__(*args, **kwargs)
    if "channelId" not in db:
      db["channelId"] = int(os.getenv("NOTIFY_CHANNEL"))
    
    self.notificationChannel = None #Initialized in setup_loop
    self.tagId = os.getenv("TAG")

    self.scheduler = AsyncIOScheduler({'apscheduler.timezone': 'UTC'})

    self.update_info.start()
  

  async def alert_exploration(self):
    '''
    Sends a message to the notification channel when
    the exploration finishes.
    '''
    print("Alert <@&{}>: Exploration done.".format(self.tagId))
    await self.notificationChannel.send("Expedition done!")


  async def alert_test(self):
    '''
    Debugging method for sending test message
    '''
    print("Alert test")
    await self.notificationChannel.send("Test alert <@&{}>".format(self.tagId))
  

  @tasks.loop(minutes=5)
  async def update_info(self):
    '''
    Updates the database from the API server, sends messages if
    tiles change, and starts a timer for kd expeditions if one 
    is running.
    '''
    #print("{}> Updating info".format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
    success = False

    #Update to database
    data = await self.get_qs_data()
    if(data):
      try:
        await self.update_tile_status(data["kingdom"]["tiles"])
        if("mapMisc" in data["kingdom"]):
          db["mystery"] = data["kingdom"]["mapMisc"]["mystery_tile"]
        db["exploration_timer"] = data["kingdom"]["activeExploration"]["exploration_timer"]
        db["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        success = True
      except KeyError as e:
        await self.notificationChannel.send("Failed to index {} in API data".format(str(e)))
    else:  
      print("{}> Failed to get API data".format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))

    # Start exploration timer if there isn't one
    if len(self.scheduler.get_jobs()) == 0 and not self.is_exploration_done():
      end = self.get_exploration_date()
      self.scheduler.add_job(self.alert_exploration, "date", run_date=end, id='exploration')
      #self.scheduler.add_job(self.alert_test, "interval", minutes=1, id='exploration') #Debugging alerts
      print("Starting alert for {} UTC...".format(end))
      self.scheduler.start()
    
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
      async with session.get('https://queslar.com/api/player/full/'+os.getenv('QS_KEY')) as res:
        if res.status == 200:
          return await res.json()
        else:
          print("Server error: {}".format(res.status))
          return {}


  async def update_tile_status(self, newTiles):
    '''
    Sends a message to the notification channel if 
    tiles have changed since the last update.
    It uses newTiles and the database's tiles for
    comparison.
    '''
    i, j = 0, 0
    lost, gained = [], []
    oldTiles = db["tiles"]
    # Iterate through the tiles and compare changes
    while i < len(oldTiles) and j < len(newTiles):
      if oldTiles[i]["id"] == newTiles[j]["id"]:
        i += 1
        j += 1
      elif oldTiles[i]["id"] < newTiles[j]["id"]:
        lost.append((oldTiles[i]["id"], self.get_tile_str(oldTiles[i])))
        i += 1
      else:
        gained.append((newTiles[j]["id"], self.get_tile_str(newTiles[j])))
        j += 1
    if len(oldTiles) < len(newTiles):
      gained += [(tile["id"], self.get_tile_str(tile)) for tile in newTiles[j:]]
    elif len(oldTiles) > len(newTiles):
      lost += [(tile["id"], self.get_tile_str(tile)) for tile in oldTiles[i:]]
    
    #Send result to channel
    await self.post_tile_update(gained, lost)
    db["tiles"] = newTiles #Update db after finishing


  def is_exploration_done(self):
    '''
    Returns True if the exploration time in the database
    has passed. 
    '''
    return datetime.utcnow() > self.get_exploration_date()


  def set_notification_channel(self, channel):
    '''
    Sets the notification channel to the given channel.
    '''
    db["channelId"] = channel.id
    self.notificationChannel = channel


  def get_exploration_date(self):
    '''
    Returns a datetime format of the exploration timer.
    Note: Return type is not a string but a date
    Database format: 2021-04-07T06:13:29.000Z
    datetime format: 2021-04-07 06:13:29
    '''
    return datetime.strptime(db["exploration_timer"], "%Y-%m-%dT%H:%M:%S.000Z")


  def get_time_remaining(self):
    '''
    Returns the time remaining until the exploration finishes.
    '''
    diff = self.get_exploration_date() - datetime.utcnow()
    days, seconds = diff.days, diff.seconds
    hours = (days * 24 + seconds // 3600) % 24
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    return "{} days {} hours {} minutes {} seconds".format(days, hours, minutes, seconds)


  def to_coords(self, index):
    '''
    Returns a string representation of (column,row) 
    given an index (from the map)
    '''
    y = (index - 1) // 5 + 1
    x = (index - 1) % 5 + 1
    return "({},{})".format(x, y)  


  def get_tiles(self):
    '''
    Returns an embed featuring all tiles held by the kd
    '''
    embed = discord.Embed(title="Kingdom Tiles", color=0x0080c0)
    for tile in db["tiles"]:
      tileType = self.get_tile_str(tile)
        
      embed.add_field(name=self.to_coords(tile["id"]), value=tileType, inline=True)
    embed.set_footer(text="Last updated: {} UTC".format(db["last_updated"]))
    return embed

  def get_tile_str(self, tile):
    '''
    Returns the string representation of a tile
    '''
    if tile["type"] == "Minor" or tile["name"] == "Wild":
      if tile["resource_one_type"] == "mystery":
        tileType = "mystery({}) {}%".format(db["mystery"], tile["resource_one_value"])
      else:
        tileType = "{} {}%".format(tile["resource_one_type"], tile["resource_one_value"])
    else:  #Major tile
      tileType = "{} {}%, {} {}%, {} {}%".format(tile["resource_one_type"],tile["resource_one_value"],tile["resource_two_type"],tile["resource_two_value"],tile["resource_three_type"],tile["resource_three_value"])
    return tileType


  async def post_tile_update(self, gained, lost):
    '''
    Sends an embed message to the notification channel if 
    any tiles were lost or gained since the last update. 
    ''' 
    if len(gained) == 0 and len(lost) == 0:
      return
    
    if len(gained) != 0:
      gainedMsg = discord.Embed(title="Tile(s) Gained:", color=0x00ff00)
      for position, boostType in gained:
        gainedMsg.add_field(name=self.to_coords(position), value=boostType, inline=False)
      await self.notificationChannel.send(embed=gainedMsg)

    if len(lost) != 0:
      lostMsg = discord.Embed(title="Tile(s) Lost:", color=0xce0000)
      for position, boostType in lost:
        lostMsg.add_field(name=self.to_coords(position), value=boostType, inline=False)
      await self.notificationChannel.send("<@&{}>".format(self.tagId) , embed=lostMsg)