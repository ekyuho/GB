# start.py
# date : 2022-05-06
# 리소스 생성

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
    if cnt in {'config','info','data'}:
        url = F"http://{host}:7579/{cse['name']}/{aename}/{cnt}/{subcnt}"
        body["m2m:cin"]["con"] = ae[aename][cnt][subcnt]
    else:
        url = F"http://{host}:7579/{cse['name']}/{aename}/{cnt}"
        body["m2m:cin"]["con"] = ae[aename][cnt]
    #body["m2m:cin"]["con"]["time"]=now.strftime("%Y-%m-%d %H:%M:%S")
    #print(f'{url} {json.dumps(body)[:40]}')
              
    r = requests.post(url, data=json.dumps(body), headers=h)
    if "m2m:dbg" in r.json():
        print(f'got error {r.json}')
    else:
        print(f'created {url}/{r.json()["m2m:cin"]["rn"]}', json.dumps(r.json())[:100])

# (ae.323376-TP_A1_01_X, {'info','config'})
def allci(aei, all):
    for cnti in ae[aei]:
        for subcnti in ae[aei][cnti]:
            if cnti in all:
                #print(f'{aei}/{cnti}/{subcnti}')
                ci(aei, cnti, subcnti)

if __name__== "__main__":
    doit()
