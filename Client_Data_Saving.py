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
import select
import os
import sys
import time
from time import process_time
from datetime import datetime
from paho.mqtt import client as mqtt
from events import Events
from RepeatedTimer import RepeatedTimer
import zipfile

import Periodical_status
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
worktodo=""
worktodo_param1=""

mqtt_list = conf.mqtt_list
samplerate_list = conf.samplerate_list
TOPIC_callback=f'/oneM2M/req/{cse["name"]}/#'
TOPIC_response=f'/oneM2M/resp/{cse["name"]}'
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

'''
python3 actuate.py ae.544449-AC_A1_01_X '{"cmd":"reqstate"}'

python3 actuate.py ae.544449-AC_A1_01_X '{"cmd":"setconnect","connect":{"cseip":"218.232.234.234","cseport":7579,"csename":"cse-gnrb-mon","cseid":"cse-gnrb-mon","mqttip":"218.232.234.234","mqttport":1883,"uploadip":"218.232.234.234","uploadport":80}}'

python3 actuate.py ae.544449-AC_A1_01_X '{"cmd":"settrigger","ctrigger":{"use":"Y","mode":1,"st1high":200,"bfsec":0.015,"afsec":120}}'

python3 actuate.py ae.544449-AC_A1_01_X '{"cmd":"settime","time":{"zone":"GMT+9","mode":3,"ip":"time.nist.gov","port":80,"period":600}}'

python3 actuate.py ae.544449-AC_A1_01_X '{"cmd":"setmeasure","cmeasure":{"sensitivity":20,"samplerate":100,"usefft":"Y"}'

python3 actuate.py ae.544449-AC_A1_01_X '{"cmd":"fwupdate","protocol":"HTTP","ip":"damoa.io","port":80,"path":"/update/teros.V2.23.bin"}'

'''

def save_conf():
    with open(F"{root}/config.dat","w") as f:
        f.write(json.dumps(ae),indent=4)
    print(f"wrote confg.dat")

def do_user_command(aename, jcmd):
    global mqtt_realtime, mqtt_measure
    global ae, worktodo, worktodo_param1
    cmd=jcmd['cmd']
    if cmd in {'reset','reboot'}:
        os.system("sudo reboot")
    elif cmd in {'synctime'}:
        print('nothing to sync time')
    elif cmd in {'fwupdate'}:
        url= f'{jcmd["protocol"]}://{jcmd["ip"]}:{jcmd["port"]}{jcmd["path"]}'
        print(f'fwupdate url={url}')
        r = requests.get(url)
        if not r.status_code == 200:
            print(f'got {r.code}')
            return
        print(f'downloaded {len(r.text)} bytes')
        
        if not os.path.exists(F"{root}/fwupdate"): os.makedirs(F"{root}/fwupdate")
        fname = datetime.now().strftime(f'{root}/fwupdate/%Y%m%d_%H%M%S')
        with open(fname, "w") as f: f.write(r.text)

    elif cmd in {'realstart'}:
        print('start mqtt real tx')
        mqtt_realtime=True
    elif cmd in {'realstop'}:
        print('stop mqtt real tx')
        mqtt_realtime=False
    elif cmd in {'reqstate'}:
        print("create status ci")
        Periodical_status.ci(aename, 'state')
    elif cmd in {'settrigger','setmeasure'}:
        if cmd=='settrigger':
            print(f'set ctrigger= {jcmd["ctrigger"]}')
            ae[aename]["config"]["ctrigger"]= jcmd["ctrigger"]
        else:
            print(f'set cmeasure= {jcmd["cmeasure"]}')
            ae[aename]["config"]["cmeasure"]= jcmd["cmeasure"]
        #do_config(aename)
        worktodo = do_config
        worktodo_param1 = aename
    elif cmd in {'settime'}:
        print(f'set time= {jcmd["time"]}')
        ae[aename]["config"]["time"]= jcmd["time"]
    elif cmd in {'setconnect'}:
        print(f'set {aename}/connect= {jcmd["connect"]}')
        ae[aename]["connect"]=jcmd["connect"]
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
    global mqttc
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

        resp_topic=f'{TOPIC_response}/{aename}/json'
        r = {};
        r['m2m:rsp'] = {};
        r['m2m:rsp']["rsc"] = 2001
        r['m2m:rsp']["to"] = ''
        r['m2m:rsp']["fr"] = aename
        r['m2m:rsp']["rqi"] = j["rqi"]
        r['m2m:rsp']["pc"] = '';
        mqttc.publish(resp_topic, json.dumps(r))
        print(f'response {resp_topic} {j["rqi"]}')

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
            "start":now.strftime("%Y-%m-%d %H:%M:%S.%f"),
            "samplerate":samplerate_list[sensorType],
            "count":count,
            "data":data
            }
        mqttc.publish(TOPIC_list[sensorType], json.dumps(BODY))
    

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(('127.0.0.1', 50000))
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
        client_socket.sendall("STATUS".encode())
        command=""
    elif command.startswith("CONFIG"):
        print('config')
        client_socket.sendall("CONFIG".encode())
        command=""
'''

def do_config(aename):
    global client_socket
    client_socket.sendall(("CONFIG"+json.dumps(ae[aename]["config"])).encode())

    rData = client_socket.recv(10000)
    rData = rData.decode('utf_8')
    jsonData = json.loads(rData) # jsonData : 서버로부터 받은 json file을 dict 형식으로 변환한 것

    if jsonData["Status"] == "False":
        ae[aename]["state"]["abflag"]="Y"
        ae[aename]["state"]["abtime"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ae[aename]["state"]["abdesc"]="board config failed"
        create.ci(aename, 'state','')
        return

    print(f'got result {jsonData}')

def do_capture():
    global client_socket, mqtt_measure, time_old
    global worktodo, worktodo_param1

    if not worktodo=="":
        print('call work to do')
        worktodo(worktodo_param1)
        worktodo=""
        return

    if not mqtt_measure:
        print('no measure')
        return

    t1_start=process_time()
    client_socket.sendall("CAPTURE".encode()) # deice server로 'CAPTURE' 명령어를 송신합니다.

    rData = client_socket.recv(10000)
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
