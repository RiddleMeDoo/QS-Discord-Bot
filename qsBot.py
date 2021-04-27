from discord.ext import tasks, commands
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
import aiohttp
from datetime import datetime
from replit import db
from tile import Tile
from exploration import Exploration
from market import Market

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

    self.market = Market()

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
        if "mapMisc" in data["kingdom"] and self.mystery != data["kingdom"]["mapMisc"]["mystery_tile"]:
          self.mystery = data["kingdom"]["mapMisc"]["mystery_tile"]
          db["mystery"] = self.mystery

        await self.update_tile_status(data["kingdom"]["tiles"])

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
    self.notificationChannel = self.get_channel(db.get("channelId"))
    if(not self.notificationChannel):
      print("Failed to find channel.")


  async def get_qs_data(self, key=os.environ['QS_KEY']):
    '''
    Returns player data from the API server
    '''
    async with aiohttp.ClientSession() as session:
      async with session.get('https://queslar.com/api/player/full/'+key) as res:
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
    embed.set_footer(text="Last updated: {} UTC".format(db.get("last_updated","Unknown")))
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
  

  async def get_player_investments(self, key):
    if self.market.is_outdated() and not await self.market.update():
      print("Market could not update.")
      return
    data = await self.get_qs_data(key)


    #Costs for number of partners/pets 
    buyPCost = {
      0: 0,
      1: 10000,
      2: 110000,
      3: 1110000,
      4: 11110000,
      5: 111110000,
      6: 1111110000,
      7: 11111110000
    }

    # Basic info + currencies
    currency = data["currency"]
    username = "{}({})".format(data["player"]["username"],currency["id"])
    level = data["skills"]["battling"]
    goldInv = "{} ({})".format(currency["gold"], currency["bank_gold"])
    creditsInv = "{} ({})".format(currency["credits"],currency["bank_credits"])
    relicsInv = "{} ({})".format(currency["relics"], currency["bank_relics"])

    # Investment
    ### Partners
    partners = data["partners"]
    partnerInvestment = 0
    for partner in partners:
      speed = partner["speed"]
      intelligence = partner["intelligence"]
      if speed > 0:
        # Calculations are made with "sum of consecutive integers" formula
        partnerInvestment += round(10000 * (speed * (speed + 1) / 2)) 
      if intelligence > 0:
        partnerInvestment += round(10000 * (intelligence * (intelligence + 1) / 2))

    partnerCost = buyPCost[len(partners)]
    petCost = buyPCost[len(data["pets"])] # PET

    ### Fighters
    fighters = data["fighters"]
    fighter_stats = ["health", "damage", "hit", "dodge", "defense", "crit_damage"]
    fighterInvestment = 0

    for fighter in fighters:
      for stat in fighter_stats:
        if fighter[stat] > 0: 
          fighterInvestment += round(10000 * (fighter[stat] * (fighter[stat] + 1) / 2))

    fighterCost = buyPCost[len(fighters) - 1]

    ### Equipment Slots
    eqSlots = data["equipmentSlots"]
    eqSlotLevels = [eqSlots["left_hand_level"], eqSlots["right_hand_level"], eqSlots["head_level"], eqSlots["body_level"], eqSlots["hands_level"], eqSlots["legs_level"], eqSlots["feet_level"]]
    matPrice = (self.market.prices["meat"] + self.market.prices["iron"] + self.market.prices["wood"] + self.market.prices["stone"]) #Used later
    baseCost = 250 * matPrice
    eqSlotInvestment = 0
    
    for level in eqSlotLevels:
      if level > 0:
        # Uses geometric series closed formula
        eqSlotInvestment += baseCost * ((1 - 1.1**level) / -0.1)
  
    ### Relics
    boosts = data["boosts"]
    relicPrice = self.market.prices["relics"]
    battleBoostTypes = ["critChance", "critDamage", "multistrike", "healing", "defense"]
    partnerTypes = ["hunting_boost","mining_boost","woodcutting_boost","stonecarving_boost"]
    relicBattleInvestment = 0
    relicPartnerInvestment = 0

    for boost in battleBoostTypes:
      if boosts[boost] > 0:
        relicBattleInvestment += round(10 * (boosts[boost] * (boosts[boost] + 1) / 2) * relicPrice)

    for boost in partnerTypes:
      if boosts[boost] > 0:
        relicPartnerInvestment += round(10 * (boosts[boost] * (boosts[boost] + 1) / 2) * relicPrice)
    
    ### House
    house = data["house"]
    houseUpgrades = ["chairs", "stove", "sink", "basket", "pitchfork", "shed", "fountain", "tools", "barrel"]
    houseInvestment = 0
    

    for type in houseUpgrades:
      if house[type] > 0:
        # Couldn't find a closed formula
        for i in range(house[type]):
          upgradeMats = 1000 + (1000 * (i - 1)**1.25)
          houseInvestment += upgradeMats * matPrice
    

    ### Homesteads (HS)
    homestead = data["playerHomesteadData"]
    hsLevels = {
      "fishing_level":0,
      "mine_level":0,
      "logging_level":0,
      "farm_level":0
    }

    for type in hsLevels:
      level = homestead[type]
      if level > 0:
        hsLevels[type] += level * (level + 1) / 2
      if level > 250:
        hsLevels[type] += (level - 250) * (level - 249) / 2
      if level > 500:
        hsLevels[type] += (level - 500) * (level - 499) / 2
      if level > 750:
        hsLevels[type] += (level - 750) * (level - 749) / 2
      if level > 1000:
        hsLevels[type] += (level - 1000) * (level - 999) / 2
      hsLevels[type] *= 1000
    
    homesteadInvestment = hsLevels["fishing_level"] * self.market.prices["meat"] + \
      hsLevels["mine_level"] * self.market.prices["iron"] + \
      hsLevels["logging_level"] * self.market.prices["wood"] + \
      hsLevels["farm_level"] * self.market.prices["stone"]
    

    totalInvestment = partnerInvestment + partnerCost + petCost + \
      fighterInvestment + fighterCost + eqSlotInvestment + \
      relicBattleInvestment + relicPartnerInvestment + \
      houseInvestment + homesteadInvestment


    ### Enchants and Equipment
    equipment = data["equipmentEquipped"]
    enchants = {
      "gold": [0,0],
      "experience": [0,0],
      "drop": [0,0],
      "stat": [0,0],
      "meat": [0,0],
      "iron": [0,0],
      "wood": [0,0],
      "stone": [0,0]
    }
    equipmentStats = []

    for piece in equipment:
      if piece["enchant_type"] in enchants:
        enchants[piece["enchant_type"]][1] = piece["enchant_value"]**0.425 / 2 + \
                                             enchants[piece["enchant_type"]][1]
        enchants[piece["enchant_type"]][0] += 1

      equipmentStats.append(piece["total_stats"])

    #Phew, finally putting the message together
    msg = "```Name: {}\nLevel: {}\nGold: {}\nCredits: {}\nRelics: {}\n\
    ---------------------------------------------------------------------\n\
    Partner Costs: {} ({})\nPartner Boosts: {}\n\
    Fighter Costs: {} ({})\nFighter Boosts: {}\nPet Costs: {} ({})\n\
    Equipment Slots: {}\nPartner Relic Boosts: {}\n\
    Battle Relic Boosts: {}\nTotal Relic Boosts: {}\nHome Investment: {}\n\
    Homestead Investment: {}\nHomestead Levels: M: {}, I: {}, W: {}, S: {}\n\
    ---------------------------------------------------------------------\n\
    Self Investment Total: {}\n\
    ---------------------------------------------------------------------\n\
    Exp Enchants: {}% ({})\nGold Enchants: {}% ({})\n\
    Drop Enchants: {}% ({})\Stat Enchants: {}% ({})\n\
    Res Enchants: {}% ({})\n\
    ---------------------------------------------------------------------\n\
    Left Hand Stats: {} ({})\nRight Hand Stats: {} ({})\n\
    Helmet Stats: {} ({})\nArmor Stats: {} ({})\nGloves Stats: {} ({})\n\
    Legging Stats: {} ({})\nBoots Stats: {} ({})```".format(
      username, level, goldInv, creditsInv, relicsInv, 
      partnerCost, len(partners), fighterCost, len(fighters),
      petCost, len(data["pets"]), eqSlotInvestment,
      relicPartnerInvestment, relicBattleInvestment,
      relicPartnerInvestment+relicBattleInvestment,
      houseInvestment, homesteadInvestment,
      homestead["fishing_level"], homestead["mine_level"],
      homestead["logging_level"], homestead["farm_level"],
      totalInvestment,
      enchants["experience"][1],enchants["experience"][0],
      enchants["gold"][1],enchants["gold"][0],
      enchants["drop"][1],enchants["drop"][0],
      enchants["stat"][1],enchants["stat"][0],
      enchants["meat"][1]+enchants["iron"][1]+enchants["wood"][1]+enchants["stone"][1],enchants["meat"][0]+enchants["iron"][0]+enchants["wood"][0]+enchants["stone"][0],
      equipmentStats[0], eqSlotLevels[0],
      equipmentStats[1], eqSlotLevels[1],
      equipmentStats[2], eqSlotLevels[2],
      equipmentStats[3], eqSlotLevels[3],
      equipmentStats[4], eqSlotLevels[4],
      equipmentStats[5], eqSlotLevels[5],
      equipmentStats[6], eqSlotLevels[6]
    )
    
    return msg

