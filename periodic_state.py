import sys
import os
import psutil
import shlex, subprocess
from datetime import datetime, timedelta
import time
import json
import create

import conf
host = conf.host
port = conf.port
ae = conf.ae

root=conf.root


def update(aename):
    global ae

    ae[aename]['state'] ={'battery':100,
                            'memory':0,
                            'disk':0,
                            'cpu':0,
                            'time':'yyyy-MM-dd HH:mm:ss.ffff',
                            'uptime':'?days, 13:29:34',
                            'abflag':'N',
                            #'abtime':'',
                            #'abdesc':'',
                            'solarinputvolt':0,
                            'solarinputamp':0,
                            'solarchargevolt':0,
                            'powersupply':5}

    state = ae[aename]['state']
    state['cpu']=psutil.cpu_percent()
    memory = psutil.virtual_memory()
    state['memory']=100*(memory.total-memory.available)/memory.total
    state['disk']= psutil.disk_usage('/')[3]
    state['time']= datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    sec = time.time() - psutil.boot_time()
    days=int(sec/86400)
    sec=sec%86400
    hours=int(sec/3600)
    sec=sec%3600
    mins=int(sec/60)

    state['uptime']= f'{days}, {hours}, {mins}'

    if os.path.exists('state.json'):
        with open('state.json','r')as f: j=json.load(f)
        print(f'j= {j}')
        state['battery']=j['battery']
    else:
        print('state file not ready yet')

    print('update', state)
    create.ci(aename, 'state', '')

if __name__ == "__main__":
    pass
