from discord.ext import tasks, commands
import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
load_dotenv()
import os
import aiohttp
from datetime import datetime
import json
from tile import Tile
from exploration import Exploration
from market import Market
import calculator as calc
import database as db


class QueslarBot(commands.Bot):
  '''
  This class contains all methods needed for commands
  + loop updates
  '''
  def __init__(self,  *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    self.db = db.db_get_all()

    if "channelId" not in self.db:
      self.db["channelId"] = os.environ['NOTIFY_CHANNEL']

    
    self.notificationChannel = None #Initialized in setup_loop

    self.tiles = [Tile(t) for t in self.db.get("tiles", [])]
    self.mystery = self.db.get("mystery","???")
    
    self.exploration = Exploration(self.db.get("exploration_timer","2000-01-01T00:00:00.000Z"))
    self.scheduler = AsyncIOScheduler({'apscheduler.timezone': 'UTC'})

    self.market = Market()

    self.update_info.start()
    self.scheduler.start()
  

  async def alert_exploration(self):
    '''
    Sends a message to the notification channel when
    the exploration finishes.
    '''
    print("Alert: Exploration done.")
    await self.notificationChannel.send("@here Exploration done!")


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
          self.db["mystery"] = self.mystery
          db.db_set("mystery", self.mystery) # Important to update asap
          for tile in self.tiles:
            tile.set_mystery(self.mystery)

        await self.update_tile_status(data["kingdom"]["tiles"])

        dataExplo = Exploration(data["kingdom"]["activeExploration"]["exploration_timer"])
        if self.exploration != dataExplo:
          self.db["exploration_timer"] = data["kingdom"]["activeExploration"]["exploration_timer"]
          self.exploration = dataExplo

        self.db["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
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

    # Save data to the cloud database
    db.db_set_all(self.db)
    
    return success


  @update_info.before_loop
  async def setup_loop(self):
    await self.wait_until_ready()
    #Initialize channel
    self.notificationChannel = self.get_channel(int(self.db.get("channelId")))
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
      self.db["tiles"] = tiles #Update db if anything changed


  def set_notification_channel(self, channel):
    '''
    Sets the notification channel to the given channel.
    '''
    self.db["channelId"] = channel.id
    self.notificationChannel = channel


  def get_tiles(self):
    '''
    Returns an embed featuring all tiles held by the kd
    '''
    embed = discord.Embed(title="Kingdom Tiles", color=0x0080c0)
    for tile in self.tiles:
      embed.add_field(name=tile.get_coords(), value=str(tile), inline=True)
    embed.set_footer(text="Last updated: {} UTC".format(self.db.get("last_updated","Unknown")))
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
      return "Market could not update."
    data = await self.get_qs_data(key)
    if not data: return "Player key is not valid."

    toStr = self.market.price_to_str #Because the function name is long

    # Basic info + currencies
    currency = data["currency"]
    village = data["village"]["overview"]["name"] if data["village"] else "Not in a village"
    username = "{}({})".format(data["player"]["username"],currency["id"])
    level = data["skills"]["battling"]
    goldInv = "{} ({})".format(toStr(currency["gold"]), toStr(currency["bank_gold"]))
    creditsInv = "{} ({})".format(toStr(currency["credits"]),toStr(currency["bank_credits"]))
    relicsInv = "{} ({})".format(toStr(currency["relics"]), toStr(currency["bank_relics"]))

    msg = """```Village: {}\nName: {}\nLevel: {}\nGold: {}\nCredits: {}\nRelics: {}
---------------------------------------------------------------------\n""".format(
      village, username, level, goldInv, creditsInv, relicsInv
    )

    # Basic stats
    stats = data["stats"]
    msg += """Strength: {}\nHealth: {}\nAgility: {}\nDexterity: {}
---------------------------------------------------------------------\n""".format(
      stats["strength"], stats["health"], stats["agility"], stats["dexterity"]
    )

    # Investment
    ### Partners
    partners = data["partners"]
    partnerInvestment = currency["shattered_partner_gold"]
    for partner in partners:
      partnerInvestment += calc.getPartnerInvestment(partner["speed"],partner["intelligence"])

    partnerCost = calc.getUnitInvestment(len(partners))

    ### Pets
    petCost = calc.getUnitInvestment(len(data["pets"]))
    petInvestment = calc.getPetInvestment(data["playerPetsData"])

    ### Fighters
    fighters = data["fighters"]
    fighterInvestment = currency["shattered_fighter_gold"]
    fighterCost = calc.getUnitInvestment(len(fighters) - 1)

    for fighter in fighters:
      fighterInvestment += calc.getFighterInvestment(fighter)

    ### Equipment Slots
    eqSlots = data["equipmentSlots"]
    eqSlotLevels = [eqSlots["left_hand_level"], eqSlots["right_hand_level"], eqSlots["head_level"], eqSlots["body_level"], eqSlots["hands_level"], eqSlots["legs_level"], eqSlots["feet_level"]]
    matPrice = (float(self.market.prices["meat"]) + float(self.market.prices["iron"]) + \
        float(self.market.prices["wood"]) + float(self.market.prices["stone"])) #Used later
    eqSlotInvestment = calc.getEqSlotInvestment(eqSlotLevels) * matPrice
    
    ### Cave
    cave = data["fighterCaveTools"]
    caveInvestment = 0
    caveUpgrades = ["archeology", "brush", "trowel", "map", "backpack", "torch", "scouting", "spade", "knife"]

    for tool in caveUpgrades:
      caveInvestment += round(calc.getCaveInvestment(cave[tool]) * matPrice)
   
    ### Relics
    boosts = data["boosts"]
    relicPrice = float(self.market.prices["relics"])
    battleBoostTypes = ["critChance", "critDamage", "multistrike", "healing", "defense"]
    partnerTypes = ["hunting_boost","mining_boost","woodcutting_boost","stonecarving_boost"]
    relicBattleInvestment = currency["shattered_battling_relics"] * relicPrice
    relicPartnerInvestment = currency["shattered_partner_relics"] * relicPrice

    for boost in battleBoostTypes:
      relicBattleInvestment += round(calc.getRelicInvestment(boosts[boost]) * relicPrice)

    for boost in partnerTypes:
      relicPartnerInvestment += round(calc.getRelicInvestment(boosts[boost]) * relicPrice)
    
    ### House
    house = data["house"]
    houseUpgrades = ["chairs", "stove", "sink", "basket", "pitchfork", "shed", "fountain", "tools", "barrel"]
    livingRoom = ["table","candlestick","carpet","couch"]
    houseInvestment = 0

    for deco in houseUpgrades:
      houseInvestment += calc.getHouseInvestment(house[deco]) * matPrice
    for deco in livingRoom:
      houseInvestment += calc.getHouseInvestment(house[deco], 5000000) * matPrice

    ### Homesteads (HS)
    homestead = data["playerHomesteadData"]
    hsLevels = {
      "fishing_level": "meat",
      "mine_level": "iron",
      "logging_level": "wood",
      "farm_level": "stone"
    }
    homesteadInvestment = 0

    for type in hsLevels:
      homesteadInvestment += calc.getHomesteadInvestment(homestead[type]) * \
        float(self.market.prices[hsLevels[type]])
    
    ### Pet experience (from decorations)
    decos = data.get("playerHomesteadDecorations", [])
    petExp = 0
    for decoration in decos:
      if decoration.get("pet_exp_boost", 0) > 0:
        petExp += decoration.get("pet_exp_boost", 0)


    msg += """Partner Costs: {} ({})\nPartner Boosts: {}\n
Fighter Costs: {} ({})\nFighter Boosts: {}\nCave Investment: {}\n
Pet Costs: {} ({})\nPet Boosts: {}\n
Equipment Slots: {}\nPartner Relic Boosts: {}
Battle Relic Boosts: {}\nTotal Relic Boosts: {}\nHome Investment: {}\n
Homestead Investment: {}\nHomestead Levels: M: {}, I: {}, W: {}, S: {}
Total Pet Exp Boost: {}%
---------------------------------------------------------------------\n""".format(
      toStr(partnerCost), len(partners), toStr(partnerInvestment),
      toStr(fighterCost), len(fighters), toStr(fighterInvestment), 
      toStr(caveInvestment),
      toStr(petCost), len(data["pets"]), toStr(petInvestment), 
      toStr(eqSlotInvestment), toStr(relicPartnerInvestment), 
      toStr(relicBattleInvestment), toStr(relicPartnerInvestment+relicBattleInvestment),
      toStr(houseInvestment), toStr(homesteadInvestment),
      homestead["fishing_level"], homestead["mine_level"],
      homestead["logging_level"], homestead["farm_level"],
      petExp
    )
    

    totalInvestment = partnerInvestment + partnerCost + petCost + \
      fighterInvestment + fighterCost + eqSlotInvestment + \
      relicBattleInvestment + relicPartnerInvestment + \
      houseInvestment + homesteadInvestment

    msg += """Self Investment Total: {}
---------------------------------------------------------------------\n""".format(
      toStr(totalInvestment)
    )


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
    eqDamage = 0
    eqDefense = 0
    eqTiers = {
      0: 1,
      1: 1.15, 
      2: 1.25,
      3: 1.5,
      4: 1.65,
      5: 1.9,
      6: 2.1,
      7: 2.3,
      8: 2.5,
      9: 3,
      10: 4
    }

    for piece in equipment:
      if piece.get("enchant_type","") in enchants:
        enchants[piece["enchant_type"]][1] = piece["enchant_value"]**0.425 / 2 + \
                                             enchants[piece["enchant_type"]][1]
        enchants[piece["enchant_type"]][0] += 1

      # Adding tier bonus to stats
      totalStats = round(piece["strength"] * eqTiers[piece["strength_tier"]] + \
        piece["health"] * eqTiers[piece["health_tier"]] + \
        piece["agility"] * eqTiers[piece["agility_tier"]] + \
        piece["dexterity"] * eqTiers[piece["dexterity_tier"]])
      equipmentStats.append(totalStats)

      eqDamage += round(piece["damage"] * eqTiers[piece["damage_tier"]])
      eqDefense += round(piece["defense"] * eqTiers[piece["defense_tier"]])
    

    msg += """Exp Enchants: {}% ({})\nGold Enchants: {}% ({})
Drop Enchants: {}% ({})\nStat Enchants: {}% ({})
Res Enchants: {}% ({})
---------------------------------------------------------------------\n""".format(
      round(enchants["experience"][1],2),round(enchants["experience"][0],2),
      round(enchants["gold"][1],2),round(enchants["gold"][0],2),
      round(enchants["drop"][1],2),round(enchants["drop"][0],2),
      round(enchants["stat"][1],2),round(enchants["stat"][0],2),
      round(enchants["meat"][1]+enchants["iron"][1]+enchants["wood"][1]+enchants["stone"][1],2),
      round(enchants["meat"][0]+enchants["iron"][0]+enchants["wood"][0]+enchants["stone"][0],2)
    )

    msg += """Damage: {}    Defense: {}
Left Hand Stats: {} ({}+{})\nRight Hand Stats: {} ({}+{})
Helmet Stats: {} ({}+{})\nArmor Stats: {} ({}+{})\nGloves Stats: {} ({}+{})
Legging Stats: {} ({}+{})\nBoots Stats: {} ({}+{})```""".format( 
      eqDamage, eqDefense,
      equipmentStats[0], eqSlotLevels[0], equipment[0]["slot_tier"],
      equipmentStats[1], eqSlotLevels[1], equipment[1]["slot_tier"],
      equipmentStats[2], eqSlotLevels[2], equipment[2]["slot_tier"],
      equipmentStats[3], eqSlotLevels[3], equipment[3]["slot_tier"],
      equipmentStats[4], eqSlotLevels[4], equipment[4]["slot_tier"],
      equipmentStats[5], eqSlotLevels[5], equipment[5]["slot_tier"],
      equipmentStats[6], eqSlotLevels[6], equipment[6]["slot_tier"]
    )
    
    return msg
