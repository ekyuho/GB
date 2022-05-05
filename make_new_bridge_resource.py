import requests
import json

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

print('\n2. AE 생성')
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
        "api": "0.2.481.2.0001.001.000111",
        "lbl": [],
        "rr": True,
        "poa": ["http://203.254.173.104:9727"]
        }
}
url = F"http://{host}:7579/{cse['name']}"
for k in ae:
    body["m2m:ae"]["rn"]=k
    body["m2m:ae"]["lbl"]=[k]
    r = requests.post(url, data=json.dumps(body), headers=h)
    print(json.dumps(r.json()))

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

print('\n3. Container 생성')
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
    "lbl": [],
    "mbs": 16384
  }
}

for k in ae:
    url = F"http://{host}:7579/{cse['name']}/{k}"
    for ct in ae[k]["cnt"]:
        body["m2m:cnt"]["rn"]=ct
        body["m2m:cnt"]["lbl"]=[ct]
        print(url, body)
        r = requests.post(url, data=json.dumps(body), headers=h)
        print(json.dumps(r.json()))
        for subct in ae[k]["cnt"][ct]:
            if ct=='ctrl':
                create_sub(k)
            else:
                url2 = F"http://{host}:7579/{cse['name']}/{k}/{ct}"
                body["m2m:cnt"]["rn"]=subct
                body["m2m:cnt"]["lbl"]=[subct]
                print(url2, body)
                r = requests.post(url2, data=json.dumps(body), headers=h)
                print(json.dumps(r.json()))
