# Manage database operations here
import redis
import os
import json

Connect to database
redisDB = redis.Redis(
  host=os.getenv("REDIS_HOSTNAME"),
  port=os.getenv("REDIS_PORT"),
  password=os.getenv("REDIS_PASSWORD"),
  decode_responses=True
)

# Store
def db_set(key, value):
  redisDB.set(key, json.dumps(value))

# Retrieval
def db_get(key, default=None):
  result = redisDB.get(key)
  if result is None:
    return default
  else:
    try:
      obj = json.loads(result)
      return obj
    except:
      return result

# Get all key/value pairs
def db_get_all():
  keys = redisDB.keys()
  values = redisDB.mget(keys)
  return {keys[i]:json.loads(values[i]) for i in range(len(keys))}

def db_set_all(dict):
  jsonDict = {key:json.dumps(dict[key]) for key in dict.keys()}
  redisDB.mset(jsonDict)

# Deletion
def db_del(key):
  redisDB.delete(key)