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
            "con": { }
        }
    }
    url = F"http://{host}:7579/{cse['name']}/{aename}/{cnt}/{subcnt}"
    body["m2m:cin"]["con"] = ae[aename]["cnt"][cnt][subcnt]
    #body["m2m:cin"]["con"]["time"]=now.strftime("%Y-%m-%d %H:%M:%S")
    print(f'{url} {json.dumps(body)[:40]}')
              
    r = requests.post(url, data=json.dumps(body), headers=h)
    print(r.json())
    if "m2m:dbg" in r.json():
        print(f'got error {r.json}')

# (ae.323376-TP_A1_01_X, {'info','config'})
def allci(aei, all):
    for cnti in ae[aei]["cnt"]:
        for subcnti in ae[aei]["cnt"][cnti]:
            if cnti in all:
                #print(f'{aei}/{cnti}/{subcnti}')
                ci(aei, cnti, subcnti)

if __name__== "__main__":
    doit()
