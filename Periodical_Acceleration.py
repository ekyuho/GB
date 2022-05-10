# Periodical_Acceleration.py
# date : 2022-05-06
# 작성자 : ino-on, 주수아
# 정해진 주기마다 가속도 데이터의 통계를 내, 모비우스 규약에 기반한 컨텐트인스턴스를 생성합니다.
# FFT 연산을 사용하는 경우, FFT 연산 후 peak값에 해당하는 hrz를 반환하고, data->FFT 컨텐트인스턴스를 생성합니다.

from encodings import utf_8
#from msvcrt import kbhit
import threading
import requests
import json
import os
import sys
import time
from datetime import datetime
import numpy as np

import conf
host = conf.host
port = conf.port
bridge = conf.bridge
cse = conf.cse
ae = conf.ae
samplerate = conf.samplerate_list["acc1"]

this_ae = ""

# ae리스트에서 가속도 센서의 ae이름을 가져온다
for k in ae:
    if "-AC_" in k:
        this_ae = k
        break

cmeasure = ae[this_ae]["config"]["cmeasure"]
measureperiod = cmeasure["measureperiod"] # 단위는 sec

root=conf.root

#기본적인 ae 데이터 입력

# list find_pathlist()
# 통계의 대상이 될 파일 list를 출력합니다.
# 저장되어있는 json file의 생성일자를 모두 살펴본 후, measureperiod//2의 시간동안 생성된 데이터의 path list를 골라냅니다. =
# 즉, 전체 측정 데이터의 절반정도의 데이터를 통계의 대상으로 삼습니다. 추후 변경 예정.
def find_pathlist():
    global measureperiod
    path = "./raw_data/Acceleration"
    file_list = os.listdir(path)
    present_time = time.time()
    data_path_list = list()
    for i in range (len(file_list)):
        file_time = os.path.getmtime(path+'/'+file_list[i])
        time_gap = present_time-file_time
        if time_gap <= measureperiod: # 추후 데이터 수집 범위 10분으로 고정 예정
            data_path_list.append(path+'/'+file_list[i])
            print(file_list[i])
    return data_path_list

# double FFT(data_list)
# 리스트의 가장 오래된 1024개의 데이터를 받아, FFT 연산을 시행합니다.
# cmeasure에 기록된 st1min, st1max를 기반으로 peak을 찾아내어, peak에 해당하는 헤르츠를 찾아냅니다.
def FFT(data_list):
    global samplerate
    global cmeasure

    FFT_fail = -1

    if len(data_list)<1024: # 데이터가 1024개 미만인 경우, 연산을 시행하지 않음
        print("no enough data")
        print("FFT calculation has failed")
        return FFT_fail # 마이너스값 return

    data_FFT_list = list()
    
    FFT_list = data_list[:1024] # select oldest 1024 data
    data_FFT_list_np = np.fft.fft(FFT_list)
    
    for i in range(len(data_FFT_list_np)):
        data_FFT_list.append(round(np.absolute(data_FFT_list_np[i]).item(),2))
    data_FFT_list[0] = 0
    #print(data_FFT_list)

    FFT_const = samplerate/1024
    data_FFT_X = np.arange(FFT_const, FFT_const*1025, FFT_const)
    data_peak_range = list()
    for i in range(len(data_FFT_X)):
        if data_FFT_X[i] >= cmeasure["st1min"] and data_FFT_X[i] <= cmeasure["st1max"]:
            data_peak_range.append(i)
        if data_FFT_X[i] > cmeasure["st1max"]: # 데이터가 범위를 벗어나기 시작했다면, 더이상 반복문을 수행하지 않음
            break
    # peak를 측정할 범위 내에 속하는 데이터가 전혀 없는 경우, FFT는 실패
    # 예 : st1min이 100, st1max가 1000.. 이런 식일 경우
    if len(data_peak_range) == 0: 
        print("data range error : there is no data in peak range")
        print("FFT calculation has failed")
        return FFT_fail

    peak = 0
    
    for i in range(data_peak_range):
        if peak < data_FFT_list[data_peak_range[i]]:
            peak = data_FFT_list[data_peak_range[i]]

    return data_FFT_X[data_FFT_list.index(peak)]

# def void read(string aename)
# 입력받은 aename을 가진 oneM2M 서버에 통계값을 포함한 컨텐트인스턴스 생성 명령을 보냅니다.
def read(aename):
    global cmeasure
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
                "time":now.strftime("%Y-%m-%d %H:%M:%S.%f")
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
        if cmeasure["usefft"] == "Y":
            hrz = FFT(data_list)
            if hrz != -1 : #FFT 연산에 성공한 경우에만 hrz 기록
                body_FFT = {
                    "m2m:cin":{
                        "con":{
                            "start":"임시",
                            "end":"임시",
                            "st1hz":hrz
                        }
                    }
                }
                url_fft = F"http://{host}:7579/{cse['name']}/{aename}/data/fft"
                r_fft = requests.post(url_fft, data=json.dumps(body_FFT), headers=h)
        print(url, json.dumps(r.json()))

def tick():
    read(this_ae) # 추후 conf.ae에서 ae name을 가져오는 방식으로 수정이 필요함 > 수정 완료. 테스트 진행중.
    threading.Timer(measureperiod, tick).start()
    
time.sleep(measureperiod) #실행된 후, measureperiod만큼의 시간이 지나야 첫 전송을 시행합니다.
tick()
