import requests
import json

host="218.232.234.232"  #건교부 테스트 사이트
cse={'name':'cse-gnrb-mon'}

def actuate(aename, cmd):
    print('5.Actuator')
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

actuate('ae.025745-AC_A1_01_X','{"cmd":"config","method":"{bla bla..}"}')
