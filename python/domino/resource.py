import os
import json

RESOURCES = '/DOMINO/resources'

def get_dst_server():
    js = get_resource_js('dst-server.json')
    if js is not None:
        return js.get('dst-server')
    else :
        return None

def create_sf(account_id, product, version):
      path_account = '/DOMINO/accounts'
      if os.path.exists(path_account + '/' + account_id):
         os.mkdir(path_account + '/' + account_id)

def get_resource_js(name):
    try:
        file = os.path.join(RESOURCES, name)
        with open(file, "r") as f:
            return json.load(f)
    except:
        return None

def get_resource_uri(name):
    js = get_resource_js(name)
    if js is not None:
        return js.get('uri')
    else:
        return None
#---
