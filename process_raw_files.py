# 작성자 : ino-on, 주수아
# 정해진 주기마다 가속도 데이터의 통계를 내, 모비우스 규약에 기반한 컨텐트인스턴스를 생성합니다.
# FFT 연산을 사용하는 경우, FFT 연산 후 peak값에 해당하는 hrz를 반환하고, data->FFT 컨텐트인스턴스를 생성합니다.

import json
import os
import sys
import time
from datetime import datetime, timedelta
from time import process_time
import numpy as np
import requests

import create
import conf
ae = conf.ae
root=conf.root

def sensor_type(aename):
    return aename.split('-')[1][0:2]

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
def report(aename, now):
    global root, ae
    #print(f'create ci for {aename}')
    cmeasure = ae[aename]['config']['cmeasure']
    raw_path = F"{root}/raw_data/{sensor_type(aename)}"
    save_path = F"{root}/merged_data/{sensor_type(aename)}"
    if not os.path.exists(save_path): os.makedirs(save_path)

    path_list=[]
    ofname=""
    point1 = process_time()
    print('measure time begin: 0')
    missing=0
    for i in range(0, 600): # 10분간 기간
        fname = datetime.strftime(now - timedelta(seconds=i), "%Y-%m-%d-%H%M%S")
        if os.path.exists(f'{raw_path}/{fname}'):
            path_list.append(f'{raw_path}/{fname}')
            missing=0
        else:
            print(f" compensate missing file -{i} {fname}")
            missing+=1
            if ofname == "":
                print(f"oops... can not.. {i}")
            else:
                path_list.append(f'{raw_path}/{ofname}')
        if missing>10:
            print('too many missing files. Do as it is')
            break
        ofname = fname
    start_time = datetime.strftime(now - timedelta(seconds=599), "%Y-%m-%d %H:%M:%S.%f")
    print(f"done making file list {start_time} {now}  elaped= {process_time()-point1:.1f}")

    #print(f'found {len(path_list)} 1s files')
    # 통계의 대상이 되는 모든 json file의 data를 하나의 list에 저장합니다.
    data_list = list()
    for i in range(len(path_list)-1,-1,-1):
        #print(f'file= {path_list[i]}')
        with open(path_list[i]) as f:
            json_data = json.load(f)
            if isinstance(json_data['data'], list): data_list.extend(json_data["data"])
            else: data_list.append(json_data["data"])

    if len(data_list) == 0:
        print("no data to upload. skip")
        return

    # 통계의 대상이 되는 파일이 전혀 없었을 경우, 전송을 수행하지 않습니다.
    print(f"files= {len(path_list)} data= {len(data_list)} elapsed= {process_time()-point1:.1f}")
    
    data_list_np = np.array(data_list)
    dmeasure = {}
    dmeasure['type'] = "D"
    dmeasure['time'] = datetime.strftime(now, '%Y-%m-%d %H:%M:%S.%f')
    dmeasure['min'] = np.min(data_list_np)
    dmeasure['max']= np.max(data_list_np)
    dmeasure['avg'] = np.average(data_list_np)
    dmeasure['std'] = np.std(data_list_np)
    dmeasure['rms'] = np.sqrt(np.mean(data_list_np**2))
    ae[aename]['data']['dmeasure'] = dmeasure
    create.ci(aename, 'data', 'dmeasure')
    
    if cmeasure["usefft"] in {"Y", "y"}:
        hrz = FFT(cmeasure, data_list_np)
        if hrz != -1 : #FFT 연산에 성공한 경우에만 hrz 기록
            fft = {}
            fft["start"]=start_time
            fft["end"]=datetime.strftime(now, '%Y-%m-%d %H:%M:%S.%f')
            fft["st1hz"]=hrz
            ae[aename]['data']['fft']=fft
            create.ci(aename, 'data', 'fft')

    merged_file = { # 최종적으로 rawperiod간의 데이터가 저장될 json의 dict
        "starttime":start_time,
        "endtime":datetime.strftime(now, '%Y-%m-%d %H:%M:%S.%f'),
        "count":len(data_list),
        "data":data_list
    }
    file_name = f'{aename}_{now.strftime("%Y%m%d%H%M")}'
    with open (F"{save_path}/{file_name}.bin", "w") as f:
        json.dump(merged_file, f, indent=4) # 통합 data 저장. 분단위까지 파일명에 기록됩니다

    host = ae[aename]['config']['connect']['uploadip']
    port = ae[aename]['config']['connect']['uploadport']
    url = F"http://{host}:{port}/upload"

    print(f'upload url= {url} {save_path}/{file_name}.bin')
    r = requests.post(url, data = {"keyValue1":12345}, files = {"attachment":open(F"{save_path}/{file_name}.bin", "rb")})
    print(f'result= {r.text}')
    print(f'uploaded a file elapsed= {process_time()-point1:.1f}s')

    print(f'removing {len(path_list)} files')
    for file in path_list:
        try:
            os.remove(file) # 삭제할 파일이 존재하는 경우 삭제를 수행(에러 방지)
        except:
            print(f'failed in removing {file}')

