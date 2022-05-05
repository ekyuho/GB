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

broker = host
port = 1883

# mqtt server TOPIC
TOPIC_acc1 = F'/{cse["name"]}/ae.{bridge}-AC_A1_01_X/realtime'
TOPIC_acc2 = F'/{cse["name"]}/ae.{bridge}-AC_A1_02_X/realtime'
TOPIC_acc3 = F'/{cse["name"]}/ae.{bridge}-AC_A1_03_X/realtime'
TOPIC_dis = F'/{cse["name"]}/ae.{bridge}-DI_A1_01_X/realtime'
TOPIC_tem = F'/{cse["name"]}/ae.{bridge}-TP_A1_01_X/realtime'
TOPIC_deg = F'/{cse["name"]}/ae.{bridge}-TI_A1_01_X/realtime'

# mqtt를 사용할 것인지, 그렇다면 어느 센서의 데이터를 보낼지에 대한 딕셔너리
mqtt_list = {
    "use":"Y",
    "acc1":"Y",
    "acc2":"N",
    "acc3":"N",
    "dis":"N",
    "tem":"N",
    "deg":"N"
    }

# mqtt 데이터에 보낼 samplerate list. 정적 데이터의 경우 1초에 1개를 보내기 때문에 1, 동적 데이터의 경우 1초에 들어오는 데이터 개수만큼의 samplerate를 설정해두었다
samplerate_list = {
    "acc1":100,
    "acc2":100,
    "acc3":100,
    "dis":1,
    "tem":1,
    "deg":1
    }

TOPIC_list = {
    "acc1":TOPIC_acc1,
    "acc2":TOPIC_acc2,
    "acc3":TOPIC_acc3,
    "dis":TOPIC_dis,
    "tem":TOPIC_tem,
    "deg":TOPIC_deg
    }

# 다중 데이터의 경우, 어떤 data를 저장할지 결정해야한다
acc_axis = "x" # x, y, z중 택1
deg_axis = "x" # x, y, z중 택1
str_axis = "z" # x, y, z중 택1
dis_channel = "ch4" # ch4, ch5중 택1

#센서 별 데이터를 저장할 디렉토리 루트. 디렉토리가 미리 생성되어있지 않으면 에러메시지가 뜰 것으로 예상됨.
acc_path = "./raw_data/Acceleration"
deg_path = "./raw_data/Degree"
dis_path = "./raw_data/Displacement"
str_path = "./raw_data/Strain"
tem_path = "./raw_data/Temperature"

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

while True:
    ClientSock.sendall("CAPTURE".encode()) # 1초에 1번 socket server로 'CAPTURE' 명령어를 송신합니다.
    jsonData = ClientSock.recv(10000)
    jsonData = jsonData.decode('utf_8')
    jsonData = json.loads(jsonData) # jsonData : 서버로부터 받은 json file을 dict 형식으로 변환한 것
    if jsonData["Status"] == "False":
        print("data isn't ready yet")
    else:
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
        
        # 센서별 json file 생성
        jsonSave(deg_path, Degree_json)
        jsonSave(tem_path, Temperature_json)
        jsonSave(dis_path, Displacement_json)
        jsonSave(acc_path, Acceleration_json)
        jsonSave(str_path, Strain_json)

    #명령은 약 0.9초에 1번 보낸다            
    time.sleep(0.9)


ClientSock.close()
