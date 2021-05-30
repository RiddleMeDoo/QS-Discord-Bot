def getUnitInvestment(num):
  '''
  Returns the total amount of gold invested into buying num units.
  Units can be pets, partners, or fighters.
  '''
  return "1" * num + "0000"

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
      print(base)
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


def getEqSlotInvestment(eqSlots):
  '''
  Return the amount of res used as investment, given a list of eqSlots.
  Note that this only calculates the investment of a single res type.
  For a complete total, multiply by 4.
  '''
  eqSlotLevels = [eqSlots["left_hand_level"], eqSlots["right_hand_level"], 
      eqSlots["head_level"], eqSlots["body_level"], eqSlots["hands_level"], 
      eqSlots["legs_level"], eqSlots["feet_level"]]
  investment = 0

  for level in eqSlotLevels:
    if level > 0:
      # Uses geometric series closed formula
      investment += 250 * ((1 - 1.1**level) / -0.1)
  return investment


def getHouseInvestment(level):
  '''
  Returns the amount of a single type of res used in house upgrades,
  given the level. For a complete amount, multiply the return value
  by 4.
  '''
  if level <= 0: return 0
  investment = 0

  # Couldn't find a closed formula
  for i in range(1, level + 1):
    investment += 1000 + (1000 * (i - 1)**1.25)
  return investment
