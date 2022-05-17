import requests
import json
import sys


host="218.232.234.232"  #건교부 테스트 사이트
#host="m.damoa.io"  #건교부 테스트 사이트
cse={'name':'cse-gnrb-mon'}

def actuate(aename, cmd):
    print('Actuator')
    j=cmd
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

config_json = {
  "cmd": "setmeasure",
  "cmeasure": {
  "sensitivity": 20,
  "samplerate": "1/300",
  "usefft": "N",
  "offset": 0,
  "measureperiod": 600,
  "stateperiod": 60,
  "rawperiod": 60,
  "st1min": 2.1,
  "st1max": 2.6
  }
}
'''
  "cmeasure": {
    "sensitivity": 20,
    "samplerate": "1/300",
    "usefft": "N",
    "offset": 0,
    "measureperiod": 600,
    "stateperiod": 60,
    "rawperiod": 60,
    "st1min": 2.1,
    "st1max": 2.6
  }
'''

actuate("ae.11110000-TI_S1M_01_X", config_json)