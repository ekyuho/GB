# Periodical_Degree.py
# date : 2022-04-28
# 작성자 : ino-on, 주수아
# 정해진 주기마다 가장 최근 각도 데이터를 골라, 모비우스 규약에 기반한 컨텐트인스턴스를 생성합니다.

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
measureperiod = 10 # 단위는 sec


#host="m.damoa.io"
host="218.232.234.232"  #건교부 테스트 사이트
cse={'name':'cse-gnrb-mon'}
bridge='025742'  #교량코드
ae={}
cnt_proto={'config':{'ctrigger':{},'time':{},'cmeasure':{},'connect':{}},
           'info':{'manufacture':{}, 'install':{},'imeasure':{}},
           'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
           'state':{},
           'ctrl':{"sub":1}}
ae[F'ae.{bridge}-AC_A1_01_X']={'name':'Accelerator', 'cnt':cnt_proto}
ae[F'ae.{bridge}-AC_A1_02_X']={'name':'Accelerator', 'cnt':cnt_proto}
ae[F'ae.{bridge}-AC_A1_03_X']={'name':'Accelerator', 'cnt':cnt_proto}
ae[F'ae.{bridge}-DI_A1_01_X']={'name':'Displacement Guage', 'cnt':cnt_proto}
ae[F'ae.{bridge}-TP_A1_01_X']={'name':'Temperature', 'cnt':cnt_proto}
ae[F'ae.{bridge}-TI_A1_01_X']={'name':'Inclinometer', 'cnt':cnt_proto}
#기본적인 ae 데이터 입력

# string find_pathlist()
# 통계의 대상이 될 파일 path를 return합니다.
# 저장되어있는 json file의 생성일자를 모두 살펴본 후, 가장 최근에 생성된 파일을 골라냅니다.
def find_path():
    global measureperiod
    path = "./raw_data/Degree"
    file_list = os.listdir(path)
    present_time = time.time()
    min_value = measureperiod*100
    min_index = 0
    if len(file_list)==0:
        print("no data to upload")
        print("waiting...")
        return "0"
    else:
        
        for i in range (len(file_list)):
            file_time = os.path.getmtime(path+'/'+file_list[i])
            time_gap = present_time-file_time
            if time_gap < min_value:
                min_value = time_gap
                min_index = i
        return path+'/'+file_list[min_index]

# def void read(string aename)
# 입력받은 aename을 가진 oneM2M 서버에 데이터를 포함한 컨텐트인스턴스 생성 명령을 보냅니다.
def read(aename):
    #print('6.Read sensor')
    data_path = find_path()
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
                "type":"S",
                "time":now.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    }
    url = F"http://{host}:7579/{cse['name']}/{aename}/data/dmeasure"
    #body["m2m:cin"]["con"]=str(10+random.randrange(1,20)) #랜덤값 body에 입력
    
    if data_path != '0':
        with open(data_path) as f:
            json_data = json.load(f)
    
        body["m2m:cin"]["con"]["val"] = json_data["data"]
              
        r = requests.post(url, data=json.dumps(body), headers=h)
        print(url, json.dumps(r.json()))

def tick():
    read('ae.025742-TI_A1_01_X')
    threading.Timer(measureperiod, tick).start()
    
time.sleep(measureperiod)
tick()


