from datetime import datetime

def getUnitInvestment(num):
  '''
  Returns the total amount of gold invested into buying num units.
  Units can be pets, partners, or fighters.
  '''
  return int("1" * num + "0000")


def getPlotInvestment(num):
  '''
  Returns the total amount of res invested into buying num plots.
  '''
  return 0 if num <= 1 else int("2500" + "0" * num)


def getRelicInvestment(level):
  '''
  Returns the amount of relics invested according to the level
  '''
  if level <= 0:
    return 0

  if level <= 5000:
    return 10 * (level * (level + 1) / 2)
  elif level <= 10000:
    investment = 125025000 #Investment at level 5000
    increment = 30
    initCost = 50000
    
    for i in range(5, level//1000 + 1):
      base = 1000 if level >= (i+1) * 1000 else level % (i * 1000)
      investment += increment * (base * (base + 1) / 2) + (initCost * base)
      initCost += increment * 1000
      increment += 20 #increases every 1k levels
      
  else: #level > 10k
    investment = 1050200000 #Investment at level 10,000
    increment = 130
    initCost = 400000
    
    for i in range(10, level // 1000 + 1):
      base = 1000 if level >= (i+1) * 1000 else level % (i * 1000)
      investment += increment * (base * (base + 1) / 2) + (initCost * base)
      initCost += increment * 1000
      #Past 10k, increment also starts to add in consecutive sums (n * (n+1) / 2)
      increment = (i - 7) * (i - 6) / 2 * 10 + 100
      
  return investment



def getHomesteadInvestment(level):
  '''
  Returns the amount of res invested into homestead according to the level
  '''
  if level <= 1: #Homestead levels start at 1 (and not 0)
    return 0

  if level <= 1750:
    investment = -1000 #To account for not upgrading the 1st level
    increment = 1000
    initCost = 0
    
    for i in range(level // 250 + 1):
      base = 250 if level >= (i + 1) * 250 else level % 250
      investment += increment * (base * (base + 1) / 2) + (initCost * base)
      initCost += increment * 250
      increment += 1000 #increases by 1000 every 250 levels
      
  else: #level > 1750
    investment = 4378499000 #Investment at level 1750
    increment = 8010
    initCost = 7000000
    
    for i in range(7, level // 250 + 1):
      base = 250 if level >= (i + 1) * 250 else level % 250
      investment += increment * (base * (base + 1) / 2) + (initCost * base)
      initCost += increment * 250
      #Past 1750, increment also starts to add in consecutive sums (n * (n+1) / 2)
      increment = (i - 5) * (i - 4) / 2 * 10 + (i + 2) * 1000
      

  return investment


def getPartnerInvestment(speed, intelligence):
  '''
  Returns the total amount of gold invested into partner upgrades
  given its speed and intelligence
  '''
  investment = 0
  if speed > 0:
    # Calculations are made with "sum of consecutive integers" formula
    investment += round(10000 * (speed * (speed + 1) / 2)) 
  if intelligence > 0:
    investment += round(10000 * (intelligence * (intelligence + 1) / 2))
  return investment


def getPetInvestment(petInfo):
  '''
  Returns the total amount of gold invested into pet farms given all its strengths
  '''
  return (petInfo["farm_strength"]*(petInfo["farm_strength"] + 1) / 2 + \
      petInfo["farm_health"] * (petInfo["farm_health"] + 1) / 2 + \
      petInfo["farm_agility"] * (petInfo["farm_agility"] + 1) / 2 + \
      petInfo["farm_dexterity"] * (petInfo["farm_dexterity"] + 1) / 2) * 50000


def getFighterInvestment(fighter):
  '''
  Returns the total amount of gold invested into a fighter
  The fighter dict contains levels for each stat.
  '''
  fighter_stats = ["health", "damage", "hit", "dodge", "defense", "crit_damage"]
  investment = 0
  for stat in fighter_stats:
    if fighter[stat] > 0: 
      investment += round(10000 * (fighter[stat] * (fighter[stat] + 1) / 2))

  return investment


def getEqSlotInvestment(eqSlotLevels):
  '''
  Return the amount of res used as investment, given a list of eqSlots.
  Note that this only calculates the investment of a single res type.
  For a complete total, multiply by 4.
  '''
  investment = 0

  for level in eqSlotLevels:
    if level > 0:
      # Uses geometric series closed formula
      investment += 250 * ((1 - 1.1**level) / -0.1)
  return investment


def getHouseInvestment(level, base=1000):
  '''
  Returns the amount of a single type of res used in house upgrades,
  given the level. For a complete amount, multiply the return value
  by 4.
  '''
  if level <= 0: return 0
  investment = 0

  # Couldn't find a closed formula
  for i in range(1, level + 1):
    investment += base + (base * (i - 1)**1.25)
  return investment

def getCaveInvestment(level, resPrice, diamondPrice):
  '''
  Returns a cave upgrade's investment, converting res and diamonds
  used into gold.
  '''
  diamondInvestment = level * (level + 1) / 2 * float(diamondPrice)
  return round(level * (level + 1) / 2 * 4000 * resPrice + diamondInvestment)

def getBuildingBoost(level):
  '''
  Gets the boost according to the village building's level
  '''
  return ((level // 20) * (level // 20 + 1) / 2 * 20 \
    + (level % 20) * (level // 20 + 1)) / 100


def getTileBoost(tiles, boostType):
  '''
  Returns the total boost in a list of tiles, related to the type of tile 
  '''
  boost = 0
  for tile in tiles:
    if tile["resource_one_type"] == boostType:
      boost += tile["resource_one_value"]
    elif tile["resource_two_type"] == boostType:
      boost += tile["resource_two_value"]
    elif tile["resource_three_type"] == boostType:
      boost += tile["resource_three_value"]
  return boost / 100

def getGemBoost(equipped, boostType):
  '''
  Returns the total boost of a certain type, from a list of equipped items.
  Splinters are included.
  '''
  boost = 0
  for gear in equipped:
    if gear.get("gem_type", "") == boostType:
      boost += gear["gem_value"]
    elif gear.get("gem_splinter_type", "") == boostType: #Cannot have same type on gem and splinter
      if datetime.utcnow() < datetime.strptime(gear["gem_splinter_time"], "%Y-%m-%dT%H:%M:%S.000Z"):
        multiplier = 0.4
      else:
        multiplier = 0.2
      
      boost += gear["gem_level"] * multiplier

  return boost / 100


def hasVip(expiryDate):
  '''
  Return True if vip is active
  '''
  return expiryDate != '0000-00-00 00:00:00' and \
    datetime.utcnow() < datetime.strptime(expiryDate, "%Y-%m-%dT%H:%M:%S.000Z")


def getEnchantBoost(equipment, enchantType):
  '''
  Returns the boost corresponding to the enchantment type.
  '''
  boost = 0
  for piece in equipment:
    if piece.get("enchant_type","") == enchantType:
      boost += piece["enchant_value"]**0.425 / 2

  return boost / 100


def getPersonalGoldIncome(data, enchantment):
  # Current mob, Level, Enchant, Exploration, Building, Party, V-Tile, KD-Tile, village boost tile, VIP, Frenzy
  monster = data["actions"]["monster_id"]
  level = data["skills"]["battling"] / 10000

  if "kingdom" in data and "explorationBoosts" in data["kingdom"]:
    exploration = data["kingdom"]["explorationBoosts"]["gold"] / 100
    kingdomTile = getTileBoost(data["kingdom"]["tiles"], "gold")
    villageBoostTile = getTileBoost(data["kingdom"]["tiles"], "village")
  else: 
    exploration = 0
    kingdomTile = 0
    villageBoostTile = 0

  if "village" in data and "boosts" in data["village"]:
    building = getBuildingBoost(data["village"]["boosts"]["market"])
    villageTile = getTileBoost(data["village"]["tiles"], "gold")
  else:
    building = 0
    villageTile = 0
  
  if "partyPvPData" in data and "gold" in data["partyPvPData"]:
    party = data["partyPvPData"]["gold"] / 100
  else:
    party = 0

  vipExpiryDate = data["player"]["vip_time"]
  vip = 0.1 if hasVip(vipExpiryDate) else 0
  
  frenzy = getGemBoost(data["equipmentEquipped"], "frenzy")
  pve = level + enchantment + exploration + building
  pvp = party + villageTile + kingdomTile + ((1 + villageBoostTile) * building - building)
  regularGoldPerAction = round((8 + 2 * monster) * (1 + pve) * (1 + pvp) * (1 + vip))
  frenzyGoldPerAction = regularGoldPerAction
  
  numKills = 1
  for _ in range(1, int(frenzy) + 1):
    frenzyGoldPerAction += regularGoldPerAction * ((0.65**numKills) / 1.3 + 0.02)
    numKills += 1
  # Remaining % of frenzy (chance)
  frenzyGoldPerAction += regularGoldPerAction * (frenzy % 1) * ((0.65**(numKills)) / 1.3 + 0.02)
  return round(frenzyGoldPerAction)


def getHouseBoost(level):
  '''
  Returns the house boost corresponding to the level
  '''
  if level == 0: return 0

  boost = 0
  multiplier = 0
  for _ in range(1, int(level / 15) + 1):
    multiplier += 1
    boost += min(multiplier * 15, 150)
  boost += (level % 15) * min(multiplier, 10)
  return boost / 100


def getPartnerLevel(partner, resType):
  '''
  Returns the partner level corresponding to the resType
  '''
  if resType == "meat":
    return partner["hunting"]
  elif resType == "iron":
    return partner["mining"]
  elif resType == "wood":
    return partner["woodcutting"]
  else:
    return partner["stonecarving"]


def getBaseRes(stat):
  '''
  Returns the base res, which is calculated from the stat.
  '''
  baseRes = 1
  multiplier = 3

  for tempStat in range(stat, 0, -20000):
    baseRes += min(tempStat, 20000) / 100 * multiplier
    if multiplier > 0.3:
      multiplier -= 0.05 if multiplier > 1.8 else 0.1

  return baseRes


def getPartnerResIncomeHr(data):
  #boost, enchant, exploration, building, house, party, kd-tile, v-tile, v-boost tile, vip
  relicBoosts = {
    "meat": data["boosts"]["hunting_boost"] * 0.00025,
    "iron": data["boosts"]["mining_boost"] * 0.00025,
    "wood": data["boosts"]["woodcutting_boost"] * 0.00025,
    "stone": data["boosts"]["stonecarving_boost"] * 0.00025
  }
  equipment = data["equipmentEquipped"]
  enchants = {
    "meat": 0, "iron": 0, "wood": 0, "stone": 0
  }
  for piece in equipment:
    if piece.get("enchant_type","") in enchants:
      enchants[piece["enchant_type"]] = piece["enchant_value"]**0.425 / 2 + enchants[piece["enchant_type"]]

  houseUpgrades = {
    "meat": getHouseBoost(data["house"]["pitchfork"]),
    "iron": getHouseBoost(data["house"]["fountain"]),
    "wood": getHouseBoost(data["house"]["tools"]),
    "stone": getHouseBoost(data["house"]["shed"])
  }

  if "kingdom" in data and "explorationBoosts" in data["kingdom"]:
    exploration = data["kingdom"]["explorationBoosts"]["resource"] / 100
    kingdomTile = getTileBoost(data["kingdom"]["tiles"], "resource")
    villageBoostTile = getTileBoost(data["kingdom"]["tiles"], "village")
    explorationPenalty = data["kingdom"]["activeExploration"]["cost"] / 100
  else: 
    exploration = 0
    kingdomTile = 0
    villageBoostTile = 0
    explorationPenalty = 0

  if "village" in data and "boosts" in data["village"]:
    building = getBuildingBoost(data["village"]["boosts"]["mill"])
    villageTile = getTileBoost(data["village"]["tiles"], "resource")
  else:
    building = 0
    villageTile = 0
  
  if "partyPvPData" in data and "resource" in data["partyPvPData"]:
    party = data["partyPvPData"]["resource"] / 100
  else:
    party = 0

  vipExpiryDate = data["player"]["vip_time"]
  vip = 0.1 if hasVip(vipExpiryDate) else 0

  pve = exploration + building #The rest will be added later
  pvp = party + kingdomTile + villageTile + ((1 + villageBoostTile) * building - building)

  resTypes = {1:"meat", 2:"iron", 3:"wood", 4:"stone"}
  statTypes = {"meat":"strength", "iron":"health", "wood":"agility", "stone":"dexterity"}

  # Calculate res per hour for each partner
  resIncomePerHour = 0
  for partner in data["partners"]:
    resType = resTypes[partner["action_id"]]
    level = getPartnerLevel(partner, resType) / 10000
    speed = (18 / (0.1 + partner["speed"] / (partner["speed"] + 2500)))
    intelligence = partner["intelligence"]
    playerStat = data["stats"][statTypes[resType]]
    totalStat = round(
    ((20 + (intelligence / (intelligence + 250)) * 100) / 100) * playerStat \
    + partner[statTypes[resType]])

    partnerPve = pve + level + enchants[resType]/100 + houseUpgrades[resType] + relicBoosts[resType]
    totalBoost = (1 + partnerPve) * (1 + pvp) * (1 + vip)

    baseRes = getBaseRes(totalStat)
    resPerHarvest = round(baseRes * totalBoost * (1 - explorationPenalty))
    resIncomePerHour += round(resPerHarvest * (3600 / speed))


  return resIncomePerHour


def getRelicIncomeHr(data, enchantment):
  '''
  Returns the amount of relics gathered by player and partners per hour,
  given the API data and enchantment (because getting enchant % is a pain)
  '''
  dungeonLvl = data["playerFighterData"]["dungeon_level"]

  # Player
  playerLvl = data["skills"]["battling"] / 10000
  dropAmount = 225 * (1 + 0.02 * dungeonLvl) * (1 + playerLvl)

  area = data["actions"]["monster_id"] // 100 * 0.05
  
  if "kingdom" in data and "explorationBoosts" in data["kingdom"]:
    exploration = data["kingdom"]["explorationBoosts"]["drop"] / 100
    kingdomTile = getTileBoost(data["kingdom"]["tiles"], "drop")
    villageBoostTile = getTileBoost(data["kingdom"]["tiles"], "village")
  else: 
    exploration = 0
    kingdomTile = 0
    villageBoostTile = 0

  if "village" in data and "boosts" in data["village"]:
    building = getBuildingBoost(data["village"]["boosts"]["market"])
    villageTile = getTileBoost(data["village"]["tiles"], "drop")
  else:
    building = 0
    villageTile = 0
  
  if "partyPvPData" in data and "drop" in data["partyPvPData"]:
    party = data["partyPvPData"]["drop"] / 100
  else:
    party = 0

  pve = area + building + exploration + enchantment 
  pvp = party + kingdomTile + villageTile + ((1 + villageBoostTile) * building - building)

  dropChance = 0.01 * (1 + pve) * (1 + pvp)
  relicsPerHour = round(600 * dropChance * dropAmount)

  # Partners
  pve -= area # partners do not use player area
  resTypes = {1:"meat", 2:"iron", 3:"wood", 4:"stone"}
  
  for partner in data["partners"]:
    resType = resTypes[partner["action_id"]]
    level = getPartnerLevel(partner, resType) / 10000
    speed = (18 / (0.1 + partner["speed"] / (partner["speed"] + 2500)))

    dropAmount = 225 * (1 + 0.02 * dungeonLvl) * (1 + level)
    dropChance = 0.03 * (1 + pve) * (1 + pvp)
    relicsPerHour += round(dropAmount * dropChance * (3600 / speed))
  
  return relicsPerHour
    
