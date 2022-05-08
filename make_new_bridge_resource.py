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
verify_only=False
limit=200

print('\nUsing ', host)
print('\n1. CB 조회')
h={
    "Accept": "application/json",
    "X-M2M-RI": "12345",
    "X-M2M-Origin": "S",
    "Host": F'{host}'
}
url = F"http://{host}:7579/{cse['name']}"
r = requests.get(url, headers=h)
print(cse['name'], json.dumps(r.json())[:limit])

print('\n2. AE 조회')
found=False
for k in ae:
    url = F"http://{host}:7579/{cse['name']}/{k}"
    r = requests.get(url, headers=h)
    j=r.json()
    if "m2m:ae" in j:
        print(f'found existing {k}')
        print(json.dumps(r.json())[:limit])
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
    print(f'{k}', body)
    if not verify_only:
        r = requests.post(url, data=json.dumps(body), headers=h)
        print(json.dumps(r.json())[:limit])
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
        "nu": [F'mqtt://{host}/{aename}?ct=json'],
        "exc": 10
      }
    }
    
    url = F"http://{host}:7579/{cse['name']}/{aename}/ctrl?ct=json"
    print(f'      {aename}/ctrl', body)
    if not verify_only:
        r = requests.post(url, data=json.dumps(body), headers=h)
        print(json.dumps(r.json())[:limit])
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
    for ct in ae[k]:
        body["m2m:cnt"]["rn"]=ct
        body["m2m:cnt"]["lbl"]=[ct]
        print(f'  {k} {ct}')
        if not verify_only:
            r = requests.post(url, data=json.dumps(body), headers=h)
            print(json.dumps(r.json())[:limit])
            if "m2m:dbg" in r.json(): sys.exit(0)
        if ct in {'config','info','data'}:
            url2 = F"http://{host}:7579/{cse['name']}/{k}/{ct}"
            for subct in ae[k][ct]:
                body["m2m:cnt"]["rn"]=subct
                body["m2m:cnt"]["lbl"]=[subct]
                print(f'    {k}/{ct} {subct}')
                if not verify_only:
                    r = requests.post(url2, data=json.dumps(body), headers=h)
                    print(f'    {k}/{ct}',json.dumps(r.json())[:limit])
                    if "m2m:dbg" in r.json(): sys.exit(0)
        if ct=='ctrl':
            create_sub(k)
