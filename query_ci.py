import requests
import json
import sys
from datetime import datetime, timedelta

host = '218.232.234.232'
port = '7579'
cse = 'cse-gnrb-mon'
aes = ['ae.32345141-AC_S1M_01_X', 'ae.32345141-AC_S1M_02_X', 'ae.32345141-AC_S1M_03_X', 'ae.32345141-DI_S1M_01_X', 'ae.32345141-TI_S1M_01_X', 'ae.32345141-TP_S1M_01_X']
#aes = ['ae.32345141-DI_S1M_01_X']
container = 'data/dmeasure'
#container = 'state'
#container = 'info/manufacture'

def query(_ae):
    global host, port, cse, container
    url = F"http://{host}:{port}/{cse}/{_ae}/{container}?fu=1"
    h={
        "Accept": "application/json",
        "X-M2M-RI": "12345",
        "X-M2M-Origin": "S",
        "Host": F'{host}'
    }
    
    r = requests.get(url, headers=h)
    if "m2m:dbg" in r.json():
        print('error', r.json())
        sys.exit()
    
    d=r.json()["m2m:uril"]
    d.sort(reverse=True)
    
    i=1
    for x in d:
        if 'MOBIUS' in x: continue
        t=x.split('/')[-1]
        time = datetime.strptime(t, '4-%Y%m%d%H%M%S%f') + timedelta(hours=9)
        print(_ae, time)
        print(f'  http://{host}:{port}/{x}')
        i += 1
        if i>1: return

for ae in aes:
    query(ae)
    print()
