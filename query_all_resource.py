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
print(url, json.dumps(r.json()))

print('\n2. AE/Container 조회')

for k in ae:
    url2 = F"{url}/{k}"
    r = requests.get(url2, headers=h)
    #if "m2m:dbg" in r.json():
        #sys.exit()
    print(url2, json.dumps(r.json()))
    for ct in ae[k]["cnt"]:
        url3 = F"{url2}/{ct}"
        r = requests.get(url3, headers=h)
        #if "m2m:dbg" in r.json():
            #sys.exit()
        print(url3, json.dumps(r.json()))
        if ct in {'ctrigger', 'time', 'cmeasure', 'connect', 'info','install','imeasure'}:
            for subct in ae[k]["cnt"][ct]:
                url4 = F"{url3}/{subct}"
                r = requests.get(url4, headers=h)
                #if "m2m:dbg" in r.json():
                    #sys.exit()
                print(url4, json.dumps(r.json()))
