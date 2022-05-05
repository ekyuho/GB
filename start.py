# start.py
# date : 2022-05-06
# 시작시 리소스 생성

from encodings import utf_8
import requests
import json
import sys
from datetime import datetime

import conf
host = conf.host
port = conf.port
bridge = conf.bridge
cse = conf.cse
ae = conf.ae

root=conf.root

def ci(aename, cnt, subcnt):
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
    url = F"http://{host}:7579/{cse['name']}/{aename}/{cnt}/{subcnt}"
    body["m2m:cin"]["con"] = json.dumps(ae[aename]["cnt"][cnt][subcnt], ensure_ascii=False)
    print(url, body)
              
    r = requests.post(url, data=json.dumps(body), headers=h)
    print(url, json.dumps(r.json()))
    if "m2m:dbg" in r.json():
        sys.exit()

def go():
    print('doing chores for startup')
    for aei in ae:
        for cnti in ae[aei]["cnt"]:
            for subcnti in ae[aei]["cnt"][cnti]:
                if cnti in {'ctrigger', 'time', 'cmeasure', 'connect', 'info','install','imeasure'}:
                    print(f'{aei}/{cnti}/{subcnti}')
                    ci(aei, cnti, subcnti)
