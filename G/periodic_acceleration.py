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
import create

import conf
host = conf.host
port = conf.port
ae = conf.ae
root=conf.root

#기본적인 ae 데이터 입력

# list find_pathlist()
# 통계의 대상이 될 파일 list를 출력합니다.
# 저장되어있는 json file의 생성일자를 모두 살펴본 후, measureperiod//2의 시간동안 생성된 데이터의 path list를 골라냅니다. =
# 즉, 전체 측정 데이터의 절반정도의 데이터를 통계의 대상으로 삼습니다. 추후 변경 예정.
def find_pathlist(cmeasure):
    path = F"{root}/raw_data/Acceleration"
    file_list = os.listdir(path)
    file_list.sort() # 가장 옛 파일이 가장 첫번째에 자리한다
    with open(F"{path}/{file_list[len(file_list)-1]}", "rb") as f: # 가장 최근 파일을 불러온다
        file_json = json.loads(f.read().decode('utf_8'))
        present_time = datetime.strptime(file_json["time"], "%Y-%m-%d %H:%M:%S.%f").timestamp() #가장 최근 파일의 timestamp를 적용
    #present_time = time.time()
    data_path_list = list()
    for i in range (len(file_list)):
        #print("periodic data file : ", file_list[i])
        with open (path+'/'+file_list[i], "rb") as f:
            try:
                file_json = json.loads(f.read().decode('utf_8'))
            except requests.JSONDecodeError as msg:
                print(F"ERROR : json decode has failed.\npath : '{file_list[i]}' ")
                continue
            except FileNotFoundError as msg:
                print(F"ERROR : there is no file.\npath : '{file_list[i]}' ")
                continue
            except:
                print("ERROR has occurred")
                print(F"file processing skip...\npath : '{file_list[i]}' ")
                continue
        file_time = datetime.strptime(file_json["time"], "%Y-%m-%d %H:%M:%S.%f").timestamp() #모든 파일의 timestamp를 확인
        #file_time = os.path.getmtime(path+'/'+file_list[i])
        time_gap = present_time-file_time
        if time_gap <= cmeasure["measureperiod"]: # 추후 데이터 수집 범위 10분으로 고정 예정
            data_path_list.append(path+'/'+file_list[i])
            #print(file_list[i])
    return data_path_list

# double FFT(cmeasure, data_list)
# 리스트의 가장 오래된 1024개의 데이터를 받아, FFT 연산을 시행합니다.
# cmeasure에 기록된 st1min, st1max를 기반으로 peak을 찾아내어, peak에 해당하는 헤르츠를 찾아냅니다.
def FFT(cmeasure, data_list):
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

    FFT_const = int(cmeasure["samplerate"])/1024
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
    
    for i in range(len(data_peak_range)):
        if peak < data_FFT_list[data_peak_range[i]]:
            peak = data_FFT_list[data_peak_range[i]]

    return data_FFT_X[data_FFT_list.index(peak)]

# def void read(string aename)
# 입력받은 aename을 가진 oneM2M 서버에 통계값을 포함한 컨텐트인스턴스 생성 명령을 보냅니다.
def report(aename):
    global ae
    print(f'create ci for {aename}')
    cmeasure = ae[aename]['config']['cmeasure']
    path_list = find_pathlist(cmeasure)
    path_list.sort() # 추후 fft 시작시간을 알아내기 위해 정렬
    data_list = list()

    # 통계의 대상이 되는 모든 json file의 data를 하나의 list에 저장합니다.
    for i in range(len(path_list)):
        with open(path_list[i]) as f:
            json_data = json.load(f)
            for j in range(len(json_data["data"])):
                data_list.append(json_data["data"][j])
    
    # 통계의 대상이 되는 파일이 전혀 없었을 경우, 전송을 수행하지 않습니다.
    print(f'files= {len(path_list)} data= {len(data_list)}')
    if len(data_list) == 0:
        print("no data to upload. skip")
        
    else:
        data_list = np.array(data_list)
        dmeasure = {}
        with open(path_list[0]) as f:
            json_data = json.load(f)
            start_time = json_data["time"]
        dmeasure['type'] = "D"
        dmeasure['time'] = start_time
        dmeasure['min'] = np.min(data_list)
        dmeasure['max']= np.max(data_list)
        dmeasure['avg'] = np.average(data_list)
        dmeasure['std'] = np.std(data_list)
        dmeasure['rms'] = np.sqrt(np.mean(data_list**2))
        ae[aename]['data']['dmeasure'] = dmeasure
    
        create.ci(aename, 'data', 'dmeasure')
        
        if cmeasure["usefft"] in {"Y", "y"}:
            hrz = FFT(cmeasure, data_list)

            start_index = 0
            end_index = 1024#/cmeasure["samplerate"]

            with open(path_list[start_index]) as f:
                json_data = json.load(f)
                start_time = json_data["time"]

            #with open(path_list[end_index]) as f:
            with open(path_list[len(path_list)-1]) as f:
                json_data = json.load(f)
                end_time = json_data["time"]
            
            if hrz != -1 : #FFT 연산에 성공한 경우에만 hrz 기록
                fft = {}
                fft["start"]=start_time
                fft["end"]=end_time
                fft["st1hz"]=hrz
                ae[aename]['data']['fft']=fft
                create.ci(aename, 'data', 'fft')
