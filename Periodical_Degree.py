# Periodical_Status.py
# date : 2022-05-06

from encodings import utf_8
import threading
import requests
import json
import os
import sys
import time
from datetime import datetime

measuring = True
measureperiod = 10 # 단위는 sec

import conf
host = conf.host
port = conf.port
bridge = conf.bridge
cse = conf.cse
ae = conf.ae

root=conf.root

def read(aename):
    #print('6.Read sensor')
    data_path = find_path()
    now = datetime.now()
    h={
        "Accept": "application/json",
        "X-M2M-RI": "12345",
        "X-M2M-Origin": "S",
        "Host": F'{host}',
        "Content-Type":"application/vnd.onem2m-res+json;ty=4"
    }
    body={
        "m2m:cin":
        {
            "con": {
                "type":"S",
                "time":now.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    }
    url = F"http://{host}:7579/{cse['name']}/{aename}/data/dmeasure"
    #body["m2m:cin"]["con"]=str(10+random.randrange(1,20)) #랜덤값 body에 입력
    
    if data_path != '0':
        with open(data_path) as f:
            json_data = json.load(f)
    
        body["m2m:cin"]["con"]["val"] = json_data["data"]
              
        r = requests.post(url, data=json.dumps(body), headers=h)
        print(url, json.dumps(r.json()))

def tick():
    read('ae.025742-TI_A1_01_X')
    threading.Timer(measureperiod, tick).start()
    
time.sleep(measureperiod)
tick()


