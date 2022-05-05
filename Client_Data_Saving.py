# Client_Data_Saving.py
# date : 2022-04-28
# 작성자 : ino-on, 주수아
# 소켓 서버로 'CAPTURE' 명령어를 1초에 1번 보내, 센서 데이터값을 받습니다.
# 받은 데이터를 센서 별로 분리해 각각 다른 디렉토리에 저장합니다.
# 현재 mqtt 전송도 이 프로그램에서 담당하고 있습니다.

from encodings import utf_8
#import threading
import random
import requests
import json
from socket import *
import os
import sys
import time
from datetime import datetime
from paho.mqtt import client as mqtt

import conf
broker = conf.host
port = conf.port
bridge = conf.bridge
cse = conf.cse
ae = conf.ae

root=conf.root

# mqtt server TOPIC
TOPIC_acc1 = conf.TOPIC_acc1
TOPIC_acc2 = conf.TOPIC_acc2
TOPIC_acc3 = conf.TOPIC_acc3
TOPIC_dis = conf.TOPIC_dis
TOPIC_tem = conf.TOPIC_tem
TOPIC_deg = conf.TOPIC_deg

mqtt_list = conf.mqtt_list
samplerate_list = conf.samplerate_list
TOPIC_list = conf.TOPIC_list

# 다중 데이터의 경우, 어떤 data를 저장할지 결정해야한다
acc_axis = "x" # x, y, z중 택1
deg_axis = "x" # x, y, z중 택1
str_axis = "z" # x, y, z중 택1
dis_channel = "ch4" # ch4, ch5중 택1

#센서별 데이타 저장소, 디렉토리가 없으면 자동생성
acc_path = F"{root}/raw_data/Acceleration"
deg_path = F"{root}/raw_data/Degree"
dis_path = F"{root}/raw_data/Displacement"
str_path = F"{root}/raw_data/Strain"
tem_path = F"{root}/raw_data/Temperature"
if not os.path.exists(F"{root}/raw_data"): os.makedirs(F"{root}/raw_data")
if not os.path.exists(acc_path): os.makedirs(acc_path)
if not os.path.exists(deg_path): os.makedirs(deg_path)
if not os.path.exists(dis_path): os.makedirs(dis_path)
if not os.path.exists(str_path): os.makedirs(str_path)
if not os.path.exists(tem_path): os.makedirs(tem_path)

# dict jsonCreate(dataTyep, timeData, realData)
# 받은 인자를 통해 딕셔너리를 생성합니다.
def jsonCreate(dataType, timeData, realData):
    data = {
        "type":dataType,
        "time":timeData,
        "data":realData
        }
    return data

# void jsonSave(path, jsonFile)
# 받은 dict를 json으로 변환한 후, 지정된 path에 저장합니다.
# 파일명은 기본적으로 날짜
def jsonSave(path, jsonFile):
    now = datetime.now()
    with open(path+"/"+now.strftime("%Y-%m-%d-%H%M%S"), 'w') as f:
        json.dump(jsonFile, f, indent=4)
        
# void mqtt_sending(sensorType, data)
# mqtt 전송을 수행합니다. 단, mqtt 전송을 사용하지 않기로 한 센서라면, 수행하지 않습니다.
# 센서에 따라 다른 TOPIC에 mqtt 메시지를 publish합니다.
def mqtt_sending(sensorType, data):   
    if mqtt_list[sensorType]=="Y":
        now = datetime.now()
        test_list = list()
        if type(data) == type(test_list):
            count = len(data)
        else:
            count = 1
        BODY = {
            "start":now.strftime("%Y-%m-%d-%H:%M:%S.%F"),
            "samplerate":samplerate_list[sensorType],
            "count":count,
            "data":data
            }
        mqttc.publish(TOPIC_list[sensorType], json.dumps(BODY))
    

ClientSock = socket(AF_INET, SOCK_STREAM)
ClientSock.connect(('127.0.0.1', 50000))
print("연결에 성공했습니다.")

# mqtt 전송을 사용하기로 했다면 mqtt connection을 구축합니다.
if mqtt_list["use"] == "Y":
    mqttc = mqtt.Client("Realtime Transmission")
    mqttc.connect(broker, port)

time_old=datetime.now()
while True:
    ClientSock.sendall("CAPTURE".encode()) # 0.9초에 1번 socket server로 'CAPTURE' 명령어를 송신합니다.
    jsonData = ClientSock.recv(10000)
    jsonData = jsonData.decode('utf_8')
    jsonData = json.loads(jsonData) # jsonData : 서버로부터 받은 json file을 dict 형식으로 변환한 것
    now=datetime.now()
    if jsonData["Status"] == "False":
        print("** no data", now.strftime("(%Y-%m-%d %H:%M:%S)"), f"+{(now-time_old).total_seconds()}sec")
        time_old=now
    else:
        print("data ok", now.strftime("(%Y-%m-%d %H:%M:%S)"), f"+{(now-time_old).total_seconds()}sec")
        time_old=now
        Time_data = jsonData["Timestamp"]
        Temperature_data = jsonData["Temperature"]
        Displacement_data = jsonData["Displacement"]["ch4"]
        
        acc_list = list()
        str_list = list()
        
        for i in range(len(jsonData["Acceleration"])):
            acc_list.append(jsonData["Acceleration"][i][acc_axis])
        for i in range(len(jsonData["Strain"])):
            str_list.append(jsonData["Strain"][i][str_axis])
        
        Acceleration_data = acc_list
        Strain_data = str_list
        Degree_data = jsonData["Degree"][deg_axis]
        
        # 센서의 특성을 고려해 각 센서 별로 센서 data를 담은 dict 생성
        Degree_json = jsonCreate("Degree", Time_data, Degree_data)
        Temperature_json = jsonCreate("Temperature", Time_data, Temperature_data)
        Displacement_json = jsonCreate("Displacement", Time_data, Displacement_data)
        Acceleration_json = jsonCreate("Acceleration", Time_data, Acceleration_data)
        Strain_json = jsonCreate("Strain", Time_data, Strain_data)
        
        # mqtt 전송을 시행하기로 했다면 mqtt 전송 시행
        if mqtt_list["use"] == "Y":
            mqtt_sending("acc1", Acceleration_json["data"])
            mqtt_sending("deg", Degree_json["data"])
            mqtt_sending("tem", Temperature_json["data"])
            mqtt_sending("dis", Displacement_json["data"])
            #print('publish realtime mqtt')
        
        # 센서별 json file 생성
        jsonSave(deg_path, Degree_json)
        jsonSave(tem_path, Temperature_json)
        jsonSave(dis_path, Displacement_json)
        jsonSave(acc_path, Acceleration_json)
        jsonSave(str_path, Strain_json)
	

    #명령은 약 0.9초에 1번 보낸다            
    time.sleep(0.9)


ClientSock.close()
