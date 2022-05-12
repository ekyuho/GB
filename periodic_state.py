from encodings import utf_8
import requests
import threading
import json
import sys
import os
import psutil
import shlex, subprocess
from datetime import datetime
import create

import conf
host = conf.host
port = conf.port
cse = conf.cse
ae = conf.ae

root=conf.root


def update(aename):
    ae[aename]['state'] ={'battery':100,'memory':0,'disk':0,'cpu':0,'time':'yyyy-MM-dd HH:mm:ss.ffff','uptime':'?days, 13:29:34','abflag':'N','abtime':'','abdesc':'','solarinputvolt':0,'solarinputamp':0,'solarchargevolt':0,'powersupply':5}

    state = ae[aename]['state']
    state['memory']=psutil.virtual_memory()[2]
    state['cpu']=psutil.cpu_percent()
    state['disk']= psutil.disk_usage('/')[3]
    state['time']= datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cmd = "uptime -p"
    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    output = p.communicate()[0].decode('utf8').strip()
    state['uptime']= output.replace(' hours, ',':').replace(' minutes','').replace('\n','')
    create.ci(aename, 'state', '')

def report():
    for aei in ae:
        cnti ='state'
        #print(f'{aei}/{cnti}')
        update(aei)
        create.ci(aei, cnti,'')

if __name__ == "__main__":
    report()
