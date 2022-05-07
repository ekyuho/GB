# Client_Data_Saving.py
# date : 2022-04-28
# 작성자 : ino-on, 주수아
# 소켓 서버로 'CAPTURE' 명령어를 1초에 1번 보내, 센서 데이터값을 받습니다.
# 받은 데이터를 센서 별로 분리해 각각 다른 디렉토리에 저장합니다.
# 현재 mqtt 전송도 이 프로그램에서 담당하고 있습니다.

from encodings import utf_8
import threading
from threading import Timer
import random
import requests
import json
from socket import *
import os
import sys
import time
from time import process_time
from datetime import datetime
from paho.mqtt import client as mqtt
from events import Events
from RepeatedTimer import RepeatedTimer

import create  #for Mobius resource
import conf
broker = conf.host
port = conf.port
bridge = conf.bridge
cse = conf.cse
ae = conf.ae

mqtt_realtime=True
mqtt_measure=True


root=conf.root

# mqtt server TOPIC
TOPIC_acc1 = conf.TOPIC_acc1
TOPIC_acc2 = conf.TOPIC_acc2
TOPIC_acc3 = conf.TOPIC_acc3
TOPIC_dis = conf.TOPIC_dis
TOPIC_tem = conf.TOPIC_tem
TOPIC_deg = conf.TOPIC_deg

TOPIC_callback="/oneM2M/req/cse-gnrb-mon/#"

mqtt_list = conf.mqtt_list
samplerate_list = conf.samplerate_list
TOPIC_list = conf.TOPIC_list
mqttc=""
command=""

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


def do_user_command(ae, jcmd):
    global mqtt_realtime, mqtt_measure
    cmd=jcmd['cmd']
    if cmd in {'reset'}:
        create.allci(ae, {'info','config'})
    elif cmd in {'reboot'}:
        create.allci(ae, {'state'})
    elif cmd in {'synctime'}:
        pass
    elif cmd in {'fwupdate'}:
        pass
    elif cmd in {'realstart'}:
        print('start mqtt real tx')
        mqtt_realtime=True
    elif cmd in {'realstop'}:
        print('stop mqtt real tx')
        mqtt_realtime=False
    elif cmd in {'reqstate'}:
        create.allci(ae, {'state'})
    elif cmd in {'settrigger'}:
        pass
    elif cmd in {'settime'}:
        pass
    elif cmd in {'setmeasure'}:
        pass
    elif cmd in {'setconnect'}:
        pass
    elif cmd in {'measurestart'}:
        print('start regular measure tx')
        mqtt_measure=True
    elif cmd in {'measurestop'}:
        print('stop regular measure tx')
        mqtt_measure=False
        
'''
    ClientSock.sendall(jcmd["cmd"].encode())

    rData = ClientSock.recv(10000).decode('utf_8')
    j = json.loads(rData)

    if j["Status"] == "False":
        print(f' failed {json.dumps(j)}')
        return
    print(j)
'''



def got_callback(topic, msg):
    # 무슨이유인지 4 or 5 두개가 왔다갔다... ㅠ  보고 처리요망
    # m.damoa.io는 5,  건기원은 4
    aename=topic[5] 
    if aename in ae:
        #print(topic, aename,  msg)
        try:
            j=json.loads(msg)
        except:
            print(f"json error {msg}")
            return
        jcmd=j["pc"]["m2m:sgn"]["nev"]["rep"]["m2m:cin"]["con"]
        print(f" ==> {aename} {jcmd}")
        do_user_command(aename, jcmd)
    else:
        print(' ==> not for me', topic, msg[:20],'...')
        return

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to {broker} via MQTT")
            client.subscribe(TOPIC_callback)
            print(f"subscribed to {TOPIC_callback}")
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_disconnect(client, userdata, rc):
        print("Disconnected from MQTT server!")

    def on_message(client, _topic, _msg):
        topic=_msg.topic.split('/')
        msg=_msg.payload.decode('utf8')
        got_callback(topic, msg)


    client_id = f'python-mqtt-{random.randint(0, 1000)}'
    mqttc = mqtt.Client(client_id)
    mqttc.on_connect = on_connect
    mqttc.on_disconnect = on_disconnect
    mqttc.on_message = on_message
    mqttc.connect(broker, port)
    return mqttc

mqttc = connect_mqtt()
mqttc.loop_start()

        
# void mqtt_sending(sensorType, data)
# mqtt 전송을 수행합니다. 단, mqtt 전송을 사용하지 않기로 한 센서라면, 수행하지 않습니다.
# 센서에 따라 다른 TOPIC에 mqtt 메시지를 publish합니다.
def mqtt_sending(sensorType, data):   
    if mqttc=="":
        connect_mqtt()

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

# create initial resources for Mobius
def init_resource():
    print("Create init resource:")
    for x in list(ae.keys()):
        print(f" for {x}")
        create.allci(x, {'ctrigger', 'time', 'cmeasure', 'connect', 'info','install','imeasure'})


time_old=datetime.now()
'''
while True:
    if command.startswith("STATUS"):
        print('status')
        ClientSock.sendall("STATUS".encode())
        command=""
    elif command.startswith("CONFIG"):
        print('config')
        ClientSock.sendall("CONFIG".encode())
        command=""
'''

def do_capture():
    global ClientSock, mqtt_measure, time_old

    if not mqtt_measure:
        print('no measure')
        return

    t1_start=process_time()
    ClientSock.sendall("CAPTURE".encode()) # deice server로 'CAPTURE' 명령어를 송신합니다.

    rData = ClientSock.recv(10000)
    t2_start=process_time()
    rData = rData.decode('utf_8')
    jsonData = json.loads(rData) # jsonData : 서버로부터 받은 json file을 dict 형식으로 변환한 것
    now=datetime.now()

    if jsonData["Status"] == "False":
        print(f' ** no data {now.strftime("%H:%M:%S")} +{(now-time_old).total_seconds():.1f} sec')
        time_old=now
        return
    
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
    if mqtt_list["use"] == "Y" and mqtt_realtime:  # mqtt_realtime is controlled from remote user
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

    print(f'CAPTURE {now.strftime("%H:%M:%S:%f")} capture,process={(t2_start-t1_start)*1000:.1f}+{(process_time()-t2_start)*1000:.1f}ms got {len(rData)}B {rData[:50]} ...')
	
# every 0.9 sec
RepeatedTimer(0.9, do_capture)
Timer(10, init_resource).start()
