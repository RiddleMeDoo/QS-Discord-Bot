import json

class Tile:
  def __init__(self,  tile):
    self.id = tile["id"]
    self.type, self.bonus = self.parse_tile(tile)


  def get_coords(self):
    '''
    Returns a string representation of (column,row) 
    given the tile index
    '''
    y = (self.id - 1) // 5 + 1
    x = (self.id - 1) % 5 + 1
    return "({},{})".format(x, y)  


  def parse_tile(self, tile):
    if tile["type"] == "Minor" or tile["name"] == "Wild":
      if tile["resource_one_type"] == "mystery":
        with open("db.txt","r") as f: #Not the best way of accessing data
          db = json.load(f)
        tileType = ["mystery({})".format(db.get("mystery"), "???")]
      else:
        tileType = [tile["resource_one_type"]]
      bonus = [tile["resource_one_value"]]

    else:  #Major tile with 3 types
      tileType = [tile["resource_one_type"],tile["resource_two_type"],tile["resource_three_type"]]
      bonus = [tile["resource_one_value"],tile["resource_two_value"],tile["resource_three_value"]]
    return tileType, bonus


  def __str__(self):
    '''
    Returns the string representation of a tile
    '''
    s = "{} {}%".format(self.type[0], self.bonus[0])
    for i in range(1, len(self.type)):
      s += ", {} {}%".format(self.type[i], self.bonus[i])
    
    return s
    