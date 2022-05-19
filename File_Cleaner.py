from ast import Return
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

path={'AC':'Acceleration', 'DI':'Displacement', 'TP':'Temperature', 'TI': 'Degree'}

def sensor_type(aename):
    return aename.split('-')[1][0:2]

# 삭제할 파일 list 생성
def delete_filepath_list(stype, cleanperiod): # 가장 최근 rawperiod간의 파일을 뽑는다
    raw_path = F"{root}/raw_data/{path[stype]}"

    file_list = os.listdir(raw_path)
    present_time = time.time()
    data_path_list = list()
    for i in range (len(file_list)):
        file_time = os.path.getmtime(raw_path+'/'+file_list[i])
        time_gap = present_time-file_time
        if time_gap >= cleanperiod*60: # 파일을 남겨둘 최대 기한을 넘기는 파일을 발견한다면, list에 추가
            data_path_list.append(raw_path+'/'+file_list[i])
            #print(file_list[i])
    return data_path_list

def file_clean(stype, cleanperiod):

    data_path_list = delete_filepath_list(stype, cleanperiod) 

    if len(data_path_list) == 0:
        print("no data to merge") #삭제할 데이터가 전혀 없는 경우, 삭제를 수행하지 않음
        return

    for file in data_path_list:
        try:
            os.remove(file) # 삭제할 파일이 존재하는 경우 삭제를 수행(에러 방지)
        except:
            print("ghost file")
    
def doit():
    global ae
    for aename in ae:
        cleanperiod = ae[aename]["config"]["cmeasure"]["rawperiod"]+5 #rawperiod보다 5분 더 여유를 두고 삭제 작업을 진행
        file_clean(sensor_type(aename), cleanperiod)

if __name__ == "__main__":
    doit()
