# Periodical_Acceleration.py
# date : 2022-04-28
# 작성자 : ino-on, 주수아
# 정해진 주기마다 가속도 데이터의 통계를 내, 모비우스 규약에 기반한 컨텐트인스턴스를 생성합니다.

from encodings import utf_8
import threading
import requests
import json
import os
import sys
import time
from datetime import datetime
import numpy as np

measuring = True
measureperiod = 20 # 단위는 sec

import conf
host = conf.host
port = conf.port
bridge = conf.bridge
cse = conf.cse
ae = conf.ae

root=conf.root

#기본적인 ae 데이터 입력

# list find_pathlist()
# 통계의 대상이 될 파일 list를 출력합니다.
# 저장되어있는 json file의 생성일자를 모두 살펴본 후, measureperiod//2의 시간동안 생성된 데이터의 path list를 골라냅니다.
def find_pathlist():
    global measureperiod
    path = "./raw_data/Acceleration"
    file_list = os.listdir(path)
    present_time = time.time()
    data_path_list = list()
    for i in range (len(file_list)):
        file_time = os.path.getmtime(path+'/'+file_list[i])
        time_gap = present_time-file_time
        if time_gap <= measureperiod and time_gap > measureperiod//2: #
            data_path_list.append(path+'/'+file_list[i])
            print(file_list[i])
    return data_path_list

# def void read(string aename)
# 입력받은 aename을 가진 oneM2M 서버에 통계값을 포함한 컨텐트인스턴스 생성 명령을 보냅니다.
def read(aename):
    #print('6.Read sensor')
    path_list = find_pathlist()
    now = datetime.now()
    h={
        "Accept": "application/json",
        "X-M2M-RI": "12345",
        "X-M2M-Origin": "S",
        "Host": F'{host}',
        "Content-Type":"application/vnd.onem2m-res+json;ty=4"
    }
    body={
        "m2m:cin":
        {
            "con": {
                "type":"D",
                "time":now.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    }
    url = F"http://{host}:7579/{cse['name']}/{aename}/data/dmeasure"
    #body["m2m:cin"]["con"]=str(10+random.randrange(1,20)) #랜덤값 body에 입력
    data_list = list()

    # 통계의 대상이 되는 모든 json file의 data를 하나의 list에 저장합니다.
    for i in range(len(path_list)):
        with open(path_list[i]) as f:
            json_data = json.load(f)
            for j in range(len(json_data["data"])):
                data_list.append(json_data["data"][j])
    
    # 통계의 대상이 되는 파일이 전혀 없었을 경우, 전송을 수행하지 않습니다.
    if len(data_list) == 0:
        print("no data to upload")
        print("waiting...")
        
    else:
    
        data_list = np.array(data_list)
        dmin = np.min(data_list)
        dmax = np.max(data_list)
        davg = np.average(data_list)
        dstd = np.std(data_list)
        drms = np.sqrt(np.mean(data_list**2))
    
        body["m2m:cin"]["con"]["min"] = dmin
        body["m2m:cin"]["con"]["max"] = dmax
        body["m2m:cin"]["con"]["avg"] = davg
        body["m2m:cin"]["con"]["std"] = dstd
        body["m2m:cin"]["con"]["rms"] = drms
        #각각의 연산을 수행한 후, body에 삽입합니다.

        r = requests.post(url, data=json.dumps(body), headers=h)
        print(url, json.dumps(r.json()))

def tick():
    read('ae.025742-AC_A1_02_X')
    threading.Timer(measureperiod, tick).start()
    
time.sleep(measureperiod) #실행된 후, measureperiod만큼의 시간이 지나야 첫 전송을 시행합니다.
tick()
