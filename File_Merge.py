from calendar import c
from encodings import utf_8
import threading
import requests
import json
import os
import sys
import time
from datetime import datetime
import numpy as np
import conf

ae = conf.ae
root = conf.root

# !!우선 1시간 단위로 합치는 작업부터 진행!!

last_timestamp = 0 # 가장 마지막으로 전송한 파일의 생성시각 timestamp

def sensor_type(aename):
    return aename.split('-')[1][0:2]

# 통합할 파일 list 작성
# 
#sensor_type : 센서가 어떤 type인지 출력. AC, TI 등
def filepath_list(aename, rawperiod): # 가장 최근 60분간의 파일을 뽑는다
    global last_timestamp 
    raw_path = F"{root}/raw_data"

    if aename == "AC" :
        raw_path+="/Acceleration"
    if aename == "DI" :
        raw_path+="/Displacement"
    if aename == "TP" :
        raw_path+="/Temperature"
    if aename == "TI" :
        raw_path+="/Degree"

    file_list = os.listdir(raw_path)
    present_time = time.time()
    data_path_list = list()
    if last_timestamp == 0 : # 최초 실행시, 데이터 생성일자에 따라 통합할 데이터를 골라낸다
        for i in range (len(file_list)):
            file_time = os.path.getmtime(raw_path+'/'+file_list[i])
            time_gap = present_time-file_time
            if time_gap <= rawperiod: # rawperiod에 따라 data를 수집한다
                data_path_list.append(raw_path+'/'+file_list[i])
                if last_timestamp < file_time:
                    last_timestamp = file_time # 가장 최근 파일의 timestamp를 기록한다. delay에 의한 누락을 방지하기 위한 작업.
                #print(file_list[i])
        return data_path_list

    else: # 최초 실행이 아닌 경우, 기존에 저장해둔 가장 마지막에 전송한 data의 생성일자를 이용해 통합할 데이터를 골라낸다
        next_timestamp = last_timestamp # 새로운 last_timestamp 갱신을 위해 새로운 변수 생성
        for i in range(len(file_list)):
            file_time = os.path.getmtime(raw_path+'/'+file_list[i])
            # 이전에 보냈던 latest 파일보다 더욱 최근 파일인 경우, 전송을 시행
            if file_time > last_timestamp:
                data_path_list.append(raw_path+'/'+file_list[i])
                #print(file_list[i])
                if next_timestamp < file_time:
                    next_timestamp = file_time # 가장 최근 파일의 timestamp를 기록한다. delay에 의한 누락을 방지하기 위한 작업.
        last_timestamp = next_timestamp # 작업이 끝나면 last_timestamp를 새로운 값으로 갱신
        return data_path_list

    

def file_save():
    
    for aename in ae:
        data_path_list = filepath_list(sensor_type(aename), ae[aename]["config"]["cmeasure"]["rawperiod"]*60)
        print(F"{aename} raw data merging...")

        if len(data_path_list) == 0:
            print("no data to merge") #통합할 데이터가 전혀 없는 경우, 통합을 수행하지 않음
            print("waiting...")



# 파일 통합작업 진행
# 
# 이후 통합한 파일 삭제
