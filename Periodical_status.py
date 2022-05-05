# start.py
# date : 2022-05-06
# 시작시 리소스 생성

from encodings import utf_8
import requests
import threading
import json
import sys
import os
import psutil
import shlex, subprocess
from datetime import datetime

import conf
host = conf.host
port = conf.port
bridge = conf.bridge
cse = conf.cse
ae = conf.ae

root=conf.root

def ci(aename, cnt):
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
                "time":now.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    }

    state={'battery':0,'memory':0,'disk':0,'cpu':0,'time':'yyyy-MM-dd HH:mm:ss.ffff','uptime':'?days, 13:29:34','abflag':'N','abtime':'','abdesc':'','solarinputvolt':0,'solarinputamp':0,'solarchargevolt':0,'powersupply':0}

    state['memory']=psutil.virtual_memory()[2]
    state['cpu']=psutil.cpu_percent()
    state['disk']= psutil.disk_usage('/')[3]
    state['time']= now.strftime("%Y-%m-%d %H:%M:%S")

    cmd = "uptime -p"
    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    output = p.communicate()[0].decode('utf8').strip()
    state['uptime']= output.replace(' hours, ',':').replace(' minutes','').replace('\n','')

    url = F"http://{host}:7579/{cse['name']}/{aename}/{cnt}"
    body["m2m:cin"]["con"] = json.dumps(state, ensure_ascii=False)
    #print(url, body)
              
    r = requests.post(url, data=json.dumps(body), headers=h)
    print(url, json.dumps(r.json()))
    if "m2m:dbg" in r.json():
        sys.exit()

def tick():
    for aei in ae:
        cnti ='state'
        print(f'{aei}/{cnti}')
        ci(aei, cnti)

    ae1 = list(ae.keys())[0]
    print(f'set interval {ae[ae1]["cnt"]["config"]["cmeasure"]["stateperiod"]}')
    threading.Timer(ae[ae1]["cnt"]["config"]["cmeasure"]["stateperiod"], tick).start()

tick()

