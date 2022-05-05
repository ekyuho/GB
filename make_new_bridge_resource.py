import requests
import json
import sys

import conf
host = conf.host
port = conf.port
bridge = conf.bridge
cse = conf.cse
ae = conf.ae

root=conf.root


print('\n1. CB 조회')
h={
    "Accept": "application/json",
    "X-M2M-RI": "12345",
    "X-M2M-Origin": "S",
    "Host": F'{host}'
}
url = F"http://{host}:7579/{cse['name']}"
r = requests.get(url, headers=h)
print(json.dumps(r.json()))

print('\n2. AE 조회')
found=False
for k in ae:
    url = F"http://{host}:7579/{cse['name']}/{k}"
    r = requests.get(url, headers=h)
    j=r.json()
    if "m2m:ae" in j:
        print(f'found existing {k}')
        print(json.dumps(r.json()))
        found = True
if found:
    print('\n이미 생성된 AE가 있으므로 종료합니다')
    sys.exit()

print('\n3. AE 생성')
h={
    "Accept": "application/json",
    "X-M2M-RI": "12345",
    "X-M2M-Origin": "S",
    "Host": F'{host}',
    "Content-Type":"application/vnd.onem2m-res+json;ty=2"
}
body={
    "m2m:ae" : {
        "rn": "",
        "api": "0.0.1",
        "rr": True
        }
}
url = F"http://{host}:7579/{cse['name']}"
for k in ae:
    body["m2m:ae"]["rn"]=k
    body["m2m:ae"]["lbl"]=[k]
    print(url, body)
    r = requests.post(url, data=json.dumps(body), headers=h)
    print(json.dumps(r.json()))
    if "m2m:dbg" in r.json(): sys.exit(0)

def create_sub(aename):
    print('  ** Subscription 생성')
    h={
        "Accept": "application/json",
        "X-M2M-RI": "12345",
        "X-M2M-Origin": "S",
        "Host": F"{host}",
        "Content-Type":"application/vnd.onem2m-res+json;ty=23"
    }
    body={
      "m2m:sub": {
        "rn": "sub",
        "enc": {
          "net": [3]
        },
        "nu": [F'mqtt://{host}/{cse["name"]}/{aename}?ct=json'],
        "exc": 10
      }
    }
    
    url = F"http://{host}:7579/{cse['name']}/{aename}/ctrl?ct=json"
    print(url, body)
    r = requests.post(url, data=json.dumps(body), headers=h)
    print(json.dumps(r.json()))
    if "m2m:dbg" in r.json(): sys.exit(0)

print('\n4. Container 생성')
h={
    "Accept": "application/json",
    "X-M2M-RI": "12345",
    "X-M2M-Origin": "S",
    "Host": F"{host}",
    "Content-Type":"application/vnd.onem2m-res+json;ty=3"
}
body={
  "m2m:cnt": {
    "rn": "",
    "lbl": []
  }
}

for k in ae:
    url = F"http://{host}:7579/{cse['name']}/{k}"
    for ct in ae[k]["cnt"]:
        body["m2m:cnt"]["rn"]=ct
        body["m2m:cnt"]["lbl"]=[ct]
        print('ct',url, body)
        r = requests.post(url, data=json.dumps(body), headers=h)
        print('ct',json.dumps(r.json()))
        if "m2m:dbg" in r.json(): sys.exit(0)
        for subct in ae[k]["cnt"][ct]:
            if ct=='ctrl':
                create_sub(k)
            else:
                url2 = F"http://{host}:7579/{cse['name']}/{k}/{ct}"
                body["m2m:cnt"]["rn"]=subct
                body["m2m:cnt"]["lbl"]=[subct]
                print('subct',url2, body)
                r = requests.post(url2, data=json.dumps(body), headers=h)
                print('subct',json.dumps(r.json()))
                if "m2m:dbg" in r.json(): sys.exit(0)
