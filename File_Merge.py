# File_Merge.py
# 1초단위의 데이터들을 생성시각에 따라, rawperiod에 기반해 하나의 data로 묶어 저장합니다.
# 파일의 생성시각을 읽어오는 방식을 사용중입니다. 파일의 timestamp를 읽어오는 방식은 너무 오래걸리기에...
# 현재 delay에 의한 데이터 누락에 대한 대책이 없음.
# 0513 추가 : http file server에 묶어 저장한 데이터를 전송하는 기능도 수행중입니다. 


from calendar import c
from encodings import utf_8
import threading
import requests
import json
import os
import sys
import time
from time import process_time
from datetime import datetime
import numpy as np

import conf

ae = conf.ae
root = conf.root

import default
path = default.path

def sensor_type(aename):
    return aename.split('-')[1][0:2]

# 통합할 파일 list 작성
def filepath_list(aename, rawperiod): # 가장 최근 rawperiod간의 파일을 뽑는다
    raw_path = F"{root}/raw_data/{path[sensor_type(aename)]}"

    file_list = os.listdir(raw_path)
    print(f'File_Merge:  processing {rawperiod} minutes {len(file_list)} files')
    present_time = time.time()
    data_path_list = list()
    for i in range (len(file_list)):
        file_time = os.path.getmtime(raw_path+'/'+file_list[i])
        time_gap = present_time-file_time
        if time_gap <= rawperiod*60: # rawperiod에 따라 data를 수집한다. 기본값 60분
            data_path_list.append(raw_path+'/'+file_list[i])
            #print(file_list[i])
    data_path_list.sort()
    print(f'File_Merge:  will merge {len(data_path_list)} files')
    return data_path_list

def file_save(aename, rawperiod):
    save_path = F"{root}/merged_data/{path[sensor_type(aename)]}"
    
    #통합 데이터를 저장할 디렉토리가 없다면 생성
    if not os.path.exists(save_path): os.makedirs(save_path)

    t1_stop = process_time()
    #통합할 데이터 list를 불러온다
    data_path_list = filepath_list(aename, rawperiod) 
    print(f'collect files: {process_time()-t1_stop:.1f}s')
    t1_stop = process_time()

    if len(data_path_list) == 0:
        print("no data to merge") #통합할 데이터가 전혀 없는 경우, 통합을 수행하지 않음
        print("waiting...")
        return

    empty_list = list() # time, data값이 dict 형태로 삽입될 배열
    
    merged_file = { # 최종적으로 rawperiod간의 데이터가 저장될 json의 dict
        "starttime":"",
        "endtime":"",
        "data":empty_list 
    }

    # 통합 대상인 파일을 하나씩 불러온다
    for file in range(len(data_path_list)):
        with open(data_path_list[file], "rb") as f:
            try:
                one_file = json.loads(f.read().decode('utf_8'))
            except requests.JSONDecodeError as msg:
                print(F"ERROR : json decode has failed.\npath : '{data_path_list[file]}' ")
                continue
            except FileNotFoundError as msg:
                print(F"ERROR : there is no file.\npath : '{data_path_list[file]}' ")
                continue
            except:
                print("ERROR has occurred")
                print(F"file processing skip...\npath : '{data_path_list[file]}' ")
                continue
            if file == 0:
                merged_file["starttime"] = one_file["time"]
            elif file == len(data_path_list)-1:
                merged_file["endtime"] = one_file["time"] # 가장 첫 파일과 가장 마지막 파일의 숫자를 기록한다
            
            data_file = {
                "time":one_file["time"],
                "data":one_file["data"]
            }

            merged_file["data"].append(data_file) # "data" value의 리스트에 data_file을 추가한다
            

    now = datetime.now()
    file_name = f'{aename}_{now.strftime("%Y%m%d%H%M")}'
    with open (F"{save_path}/{file_name}.bin", "w") as f:
        json.dump(merged_file, f, indent=4) # 통합 data 저장. 분단위까지 파일명에 기록됩니다

    print(f'merged files: {process_time()-t1_stop:.1f}s')
    t1_stop = process_time()

    host = ae[aename]['config']['connect']['uploadip']
    port = ae[aename]['config']['connect']['uploadport'] 
    url = F"http://{host}:{port}/upload"

    print(f'upload url= {url} {save_path}/{file_name}.bin')
    r = requests.post(url, data = {"keyValue1":12345}, files = {"attachment":open(F"{save_path}/{file_name}.bin", "rb")})
    print(f'result= {r.text}')
    print(f'uploaded a file: {process_time()-t1_stop:.1f}s')
        
def doit(aename):
    global ae
    rawperiod = ae[aename]["config"]["cmeasure"]["rawperiod"]
    file_save(aename, rawperiod)
