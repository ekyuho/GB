# Raw_Displacement.py
# date : 2022-05-06
# 작성자 : ino-on, 주수아
# 정해진 주기마다 http file server에 raw data를 전송합니다.

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

measureperiod = 10 # 단위는 sec. 추후 conf.py의 rawperiod로 수정요망
import conf

connect = conf.config_connect

host = connect["uploadip"]
port = 2883 # 통일성을 위해 추후 port = connect["uploadport"]로 바꿔야할듯합니다만, uploadport의 기본값이 건기연 서버의 포트와 달라(80) 임시로 상수를 입력해두었습니다.

root=conf.root

last_timestamp = 0

# list find_pathlist()
# 전송의 대상이 될 파일 list를 출력합니다.
# 저장되어있는 json file의 생성일자를 모두 살펴본 후, measureperiod동안 생성된 데이터의 path list를 골라냅니다.
def find_pathlist():
    global last_timestamp
    global measureperiod
    path = "./raw_data/Displacement"
    file_list = os.listdir(path)
    present_time = time.time()
    data_path_list = list()

    if last_timestamp == 0 : # 최초 실행시, 데이터 생성일자에 따라 전송할 데이터를 골라낸다
        for i in range (len(file_list)):
            file_time = os.path.getmtime(path+'/'+file_list[i])
            time_gap = present_time-file_time
            if time_gap <= measureperiod: # 추후 데이터 수집 범위 10분으로 고정 예정
                data_path_list.append(path+'/'+file_list[i])
                if last_timestamp < file_time:
                    last_timestamp = file_time # 가장 최근 파일의 timestamp를 기록한다. delay에 의한 누락을 방지하기 위한 작업.
                #print(file_list[i])
        return data_path_list

    else: # 최초 실행이 아닌 경우, 기존에 저장해둔 가장 마지막에 전송한 data의 생성일자를 이용해 전송할 데이터를 골라낸다
        next_timestamp = last_timestamp # 새로운 last_timestamp 갱신을 위해 새로운 변수 생성
        for i in range(len(file_list)):
            file_time = os.path.getmtime(path+'/'+file_list[i])
            # 이전에 보냈던 latest 파일보다 더욱 최근 파일인 경우, 전송을 시행
            if file_time > last_timestamp:
                data_path_list.append(path+'/'+file_list[i])
                #print(file_list[i])
                if next_timestamp < file_time:
                    next_timestamp = file_time # 가장 최근 파일의 timestamp를 기록한다. delay에 의한 누락을 방지하기 위한 작업.
        last_timestamp = next_timestamp # 작업이 끝나면 last_timestamp를 새로운 값으로 갱신
        return data_path_list


def transport():
    global host
    global port
    global last_timestamp
    path_list = find_pathlist()

    # 전송의 대상이 되는 파일이 전혀 없었을 경우, 전송을 수행하지 않습니다.
    if len(path_list) == 0:
        print("no data to upload")
        print("waiting...")

    url = F"http://{host}:{port}/upload"

    for i in range(len(path_list)): # 지정된 data path에 존재하는 모든 file에 대해 전송 시행
        r = requests.post("http://218.232.234.232:2883/upload", data = {"keyValue1":12345}, files = {"attachment":open(path_list[i], "rb")})
        print(r.text)
            
def tick():
    transport()
    threading.Timer(measureperiod, tick).start()
    
time.sleep(measureperiod)
tick()