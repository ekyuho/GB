import requests
import json

import conf
host=conf.host
bridge = conf.bridge
cse = conf.cse
ae = conf.ae

def actuate(aename, cmd):
    print('5.Actuator')
    h={
        "Accept": "application/json",
        "X-M2M-RI": "12345",
        "X-M2M-Origin": "S",
        "Host": F'{host}',
        "Content-Type":"application/vnd.onem2m-res+json; ty=4"
    }
    body={
        "m2m:cin":{
            "con": cmd
            }
    }
    url = F"http://{host}:7579/{cse['name']}/{aename}/ctrl"
    r = requests.post(url, data=json.dumps(body), headers=h)
    print(url, json.dumps(r.json()))

actuate('ae.025745-AC_A1_01_X','{"cmd":"do it","mood":"positive"}')
