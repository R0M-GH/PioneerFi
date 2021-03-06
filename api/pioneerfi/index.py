from flask import Flask, Response, request
import pymongo
from bson import json_util
import time
import hashlib

app = Flask(__name__)

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["pioneerfi"]

nodes = db["nodes"]
observations = db["observations"]

@app.route('/')
def get_observations():
  found_nodes = nodes.find({}) # get all nodes
  populated_nodes = []
  for node in found_nodes:
    node_obs = list(observations.find({"node": node["_id"]}))
    node["obs"] = node_obs
    if (len(node_obs) == 0):
      curr_status = 'down'
    else:
      curr_status = 'down' if int(time.time()) - 120 > node_obs[-1]["timestamp"] else 'up';
    status_obj = {
      'status': curr_status
    }
    if (curr_status == 'up') :
      status_obj["down"] = node_obs[-1]["download"]
      status_obj["up"] = node_obs[-1]["upload"]
      status_obj["ping"] = node_obs[-1]["ping"]
    node["curr_status"] = status_obj
    populated_nodes.append(node)

  return Response(
    json_util.dumps(populated_nodes),
    headers={"Access-Control-Allow-Origin":"*"},
    mimetype='application/json'
  )
  


@app.route('/', methods=['POST'])
def add_observation():
  print('received obs')
  obs_data = request.get_json()
  # print(obs_data)
  # todo: validate obs
  matched_node = nodes.find_one({"hostname": obs_data["hostname"]}) # find the right node by hostname
  print(matched_node)
  obs_data["node"] = matched_node["_id"] # add ref
  obs_data["timestamp"] = int(time.time()) # add timestamp
  passkey = obs_data["passkey"]
  hashed = hashlib.sha256(passkey.encode()).hexdigest()
  if (hashed == matched_node["auth-hash"]):
    iden = observations.insert_one(obs_data) # insert the observation
    print('inserted obs')
  else:
    print('insert failed - bad auth')
  return '', 204
