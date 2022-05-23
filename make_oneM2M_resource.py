import requests
import json
import sys
import create

import conf
host = conf.host
port = conf.port
csename = conf.csename
ae = conf.ae
root=conf.root
verify_only=False

def makeit():
    print('Using ', host)
    print('Query CB:')
    h={
        "Accept": "application/json",
        "X-M2M-RI": "12345",
        "X-M2M-Origin": "S",
        "Host": F'{host}'
    }
    url = F"http://{host}:7579/{csename}"
    r = requests.get(url, headers=h)
    print('found', 'm2m:cb', r.json()["m2m:cb"]["rn"])

    aename_list = list()
    for aename in ae:
        aename_list.append(aename) # 설정된 ae name을 모은 list를 따로 생성
    
    print('Query AE: ')
    #found=False
    for k in ae:
        url = F"http://{host}:7579/{csename}/{k}"
        r = requests.get(url, headers=h)
        j=r.json()
        if "m2m:ae" in j:
            print('found', r.json()["m2m:ae"]["rn"])
            if r.json()["m2m:ae"]["rn"] in aename_list:
                aename_list.remove(r.json()["m2m:ae"]["rn"]) # 정말로 설정에 존재하는 모든 AE가 존재하는지 하나씩 지워가면서 확인
            #found = True
    if len(aename_list) == 0:
        return
    
    print('Found no AE. Create fresh one')
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
    url = F"http://{host}:7579/{csename}"
    for k in ae:
        if k not in aename_list:
            print(F"{k} already exist")
            continue
        else:
            body["m2m:ae"]["rn"]=k
            body["m2m:ae"]["lbl"]=[k]
            if not verify_only:
                r = requests.post(url, data=json.dumps(body), headers=h)
                print('created m2m:ae', r.json()["m2m:ae"]["rn"])
                if "m2m:dbg" in r.json(): sys.exit(0)
    
    def create_sub(aename):
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
        
        url = F"http://{host}:7579/{csename}/{aename}/ctrl?ct=json"
        if not verify_only:
            r = requests.post(url, data=json.dumps(body), headers=h)
            print('created m2m:sub', r.json()["m2m:sub"]["rn"])
            if "m2m:dbg" in r.json(): sys.exit(0)
    
    print('\nCreate Container ')
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
        url = F"http://{host}:7579/{csename}/{k}"
        for ct in ae[k]:
            if ct == 'local':
                continue
            body["m2m:cnt"]["rn"]=ct
            body["m2m:cnt"]["lbl"]=[ct]
            if not verify_only:
                r = requests.post(url, data=json.dumps(body), headers=h)
                print(f'created m2m:cnt {k}/{r.json()["m2m:cnt"]["rn"]}')
                if "m2m:dbg" in r.json(): 
                    print(f'error in creating ct {ct}')
                    sys.exit(0)
            if ct in {'config','info','data'}:
                url2 = F"http://{host}:7579/{csename}/{k}/{ct}"
                for subct in ae[k][ct]:
                    body["m2m:cnt"]["rn"]=subct
                    body["m2m:cnt"]["lbl"]=[subct]
                    if not verify_only:
                        r = requests.post(url2, data=json.dumps(body), headers=h)
                        print(f'created m2m:cnt {k}/{ct}/{r.json()["m2m:cnt"]["rn"]}')
                        if "m2m:dbg" in r.json(): sys.exit(0)
                    
            if ct=='ctrl':
                create_sub(k)


if __name__ == "__main__":
    makeit()
