import requests
import json
import sys


host = '218.232.234.232'
port = '7579'
cse = 'cse-gnrb-mon'
aes = ['ae.32345141-AC_S1M_01_X', 'ae.32345141-AC_S1M_02_X', 'ae.32345141-AC_S1M_03_X', 'ae.32345141-DI_S1M_01_X', 'ae.32345141-TI_S1M_01_X', 'ae.32345141-TP_S1M_01_X']
#container = 'data/dmeasure'
container = 'state'


def actuate(aename, cmd):
    j=json.loads(cmd)
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
    url = F"http://{host}:{port}/{cse}/{aename}/ctrl"
    r = requests.post(url, data=json.dumps(body), headers=h)
    print(url, json.dumps(r.json()))

for ae in aes:
    actuate(ae, '{"cmd":"reqstate"}')
