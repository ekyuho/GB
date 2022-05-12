# Client_Data_Saving.py
# date : 2022-04-28
# 작성자 : ino-on, 주수아
# 소켓 서버로 'CAPTURE' 명령어를 1초에 1번 보내, 센서 데이터값을 받습니다.
# 받은 데이터를 센서 별로 분리해 각각 다른 디렉토리에 저장합니다.
# 현재 mqtt 전송도 이 프로그램에서 담당하고 있습니다.
VERSION='1.0'
print(f'Verion {VERSION}')

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
from datetime import datetime, timedelta
from paho.mqtt import client as mqtt
from events import Events
from RepeatedTimer import RepeatedTimer

import versionup
import periodic_state
import periodic_acceleration
import periodic_temperature
import periodic_degree
import periodic_displacement
import create  #for Mobius resource
import conf

import make_oneM2M_resource
make_oneM2M_resource.makeit()

import File_Merge
import File_Cleaner

broker = conf.host
port = conf.port
cse = conf.cse
ae = conf.ae

root=conf.root
worktodo=""
worktodo_param1=""
worktodo_param2=""

TOPIC_callback=f'/oneM2M/req/{cse["name"]}/#'
TOPIC_response=f'/oneM2M/resp/{cse["name"]}'
TOPIC_list = conf.TOPIC_list
mqttc=""
command=""
trigger_in_progress={}

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

def sensor_type(aename):
    return aename.split('-')[1][0:2]

# void jsonSave(path, jsonFile)
# 받은 dict를 json으로 변환한 후, 지정된 path에 저장합니다.
# 파일명은 기본적으로 날짜

def jsonSave(path, jsonFile):
    now = datetime.now()
    with open(path+"/"+now.strftime("%Y-%m-%d-%H%M%S"), 'w') as f:
        json.dump(jsonFile, f, indent=4)

def save_conf():
    with open(F"{root}/config.dat","w") as f:
        f.write(json.dumps(ae, ensure_ascii=False,indent=4))
    print(f"wrote config.dat")

def do_user_command(aename, jcmd):
    global mqtt_realtime, mqtt_measure
    global ae, worktodo, worktodo_param1, worktodo_param2
    cmd=jcmd['cmd']
    if 'reset' in cmd:
        file=f"{root}/config.dat"
        if os.path.exists(file): 
            os.remove(file)
            print(f'removed {file}')
        else:
            print(f'no {file} to delete')
        os.system("sudo reboot")
    elif 'reboot' in cmd:
        os.system("sudo reboot")
    elif cmd in {'synctime'}:
        print('nothing to sync time')
    elif cmd in {'fwupdate'}:
        url= f'{jcmd["protocol"]}://{jcmd["ip"]}:{jcmd["port"]}{jcmd["path"]}'
        versionup.versionup(url)
    elif cmd in {'realstart'}:
        print('start mqtt real tx')
        mqtt_realtime=True
    elif cmd in {'realstop'}:
        print('stop mqtt real tx')
        mqtt_realtime=False
    elif cmd in {'reqstate'}:
        print("create status ci")
        periodic_state.report()
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
        worktodo_param2 = 'save'
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
        print(f' failed {json.dumps(j, ensure_ascii=False)}')
        return
    print(j)
'''


def got_callback(topic, msg):
    global mqttc
    aename=topic[4] 
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
        r = {}
        r['m2m:rsp'] = {}
        r['m2m:rsp']["rsc"] = 2001
        r['m2m:rsp']["to"] = ''
        r['m2m:rsp']["fr"] = aename
        r['m2m:rsp']["rqi"] = j["rqi"]
        r['m2m:rsp']["pc"] = ''
        mqttc.publish(resp_topic, json.dumps(r, ensure_ascii=False))
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
print("mqtt 연결에 성공했습니다.")

        
# void mqtt_sending(aename, data)
# mqtt 전송을 수행합니다. 단, mqtt 전송을 사용하지 않기로 한 센서라면, 수행하지 않습니다.
# 센서에 따라 다른 TOPIC에 mqtt 메시지를 publish합니다.
def mqtt_sending(aename, data):   
    if mqttc=="":
        connect_mqtt()

    now = datetime.now()
    test_list = list()
    if type(data) == type(test_list):
        count = len(data)
    else:
        count = 1
    BODY = {
        "start":now.strftime("%Y-%m-%d %H:%M:%S.%f"),
        "samplerate":int(ae[aename]["config"]["cmeasure"]['samplerate']),
        "count":count,
        "data":data
        }
    mqttc.publish(F'/{cse["name"]}/{aename}/realtime', json.dumps(BODY, ensure_ascii=False))
    

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(('127.0.0.1', 50000))
print("socket 연결에 성공했습니다.")


time_old=datetime.now()

def do_config(targetae, savefile):
    global client_socket
    global ae

    setting={ 'AC':{'select':0x0100,'use':'N','st1high':0,'st1low':0, 'offset':0},
                'DI':{'select':0x0800,'use':'N','st1high':0,'st1low':0, 'offset':0},
                'TI':{'select':0x0200,'use':'N','st1high':0,'st1low':0, 'offset':0},
                'TP':{'select':0x1000,'use':'N','st1high':0,'st1low':0, 'offset':0}}
    for aename in ae:
        cmeasure = ae[aename]['config']['cmeasure']
        if 'offset' in cmeasure:
            setting[sensor_type(aename)]['offset'] = cmeasure['offset']
        ctrigger = ae[aename]['config']['ctrigger']
        if 'use' in ctrigger:
            setting[sensor_type(aename)]['use'] = ctrigger['use']
            if 'st1high' in ctrigger and str(ctrigger['st1high']).isnumeric(): setting[sensor_type(aename)]['st1high']= int(ctrigger['st1high'])
            if 'st1low' in ctrigger and str(ctrigger['st1low']).isnumeric(): setting[sensor_type(aename)]['st1low']= int(ctrigger['st1low'])

    print(f"do_config seting= {setting}")

    client_socket.sendall(("CONFIG"+json.dumps(setting, ensure_ascii=False)).encode())

    rData = client_socket.recv(10000)
    rData = rData.decode('utf_8')
    jsonData = json.loads(rData) # jsonData : 서버로부터 받은 json file을 dict 형식으로 변환한 것

    if jsonData["Status"] == "False":
        ae[aename]["state"]["abflag"]="Y"
        ae[aename]["state"]["abtime"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ae[aename]["state"]["abdesc"]="board config failed"
        create.ci(aename, 'state','')
        return

    print(f'do_config: got result {jsonData}')
    create.ci(targetae, 'state','')
    if savefile=='save':
        save_conf()

def do_trigger_followup(aename):
    global ae
    print(f'trigger_followup {aename}')
    trigger_in_progress[aename]='0'
    dtrigger=ae[aename]['data']['dtrigger']

    #아래의  function을 만들어야 합니다
    #data= merge_data(dtrigger['start'])
    data=[1,2,3,4,5]

    dtrigger['count']=len(data)
    dtrigger['data']=json.dumps(data)
    create.ci(aename, 'data', 'dtrigger')


def do_capture():
    global client_socket, mqtt_measure, time_old
    global worktodo, worktodo_param1
    global ae #samplerate 조정을 위한 값. 동적 데이터에만 적용되는 것으로 한다

    if not worktodo=="":
        print('call work to do')
        worktodo(worktodo_param1, worktodo_param2)
        worktodo=""
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
    
    #print('got=',jsonData)
    j=jsonData
    for aename in ae:
        if j['trigger'][sensor_type(aename)]=='1':
            if aename in trigger_in_progress and trigger_in_progress[aename]=='1':
                continue

            trigger_in_progress[aename]='1'
            ctrigger=ae[aename]['config']['ctrigger']
            cmeasure=ae[aename]['config']['cmeasure']
            dtrigger=ae[aename]['data']['dtrigger']
            dtrigger['time']=now.strftime("%Y-%m-%d %H:%M:%S.%f")
            dtrigger['start']=(now-timedelta(seconds=ctrigger['bfsec'])).strftime("%Y-%m-%d %H:%M:%S.%f")
            dtrigger['mode']=ctrigger['mode']
            dtrigger['sthigh']=ctrigger['st1high']
            dtrigger['stlow']=ctrigger['st1low']
            dtrigger['samplerate']=cmeasure['samplerate']
            dtrigger['val']=1

            print(f"got trigger {aename} bfsec= {ctrigger['bfsec']}  afsec= {ctrigger['afsec']}")
            if int(ctrigger['afsec']) and ctrigger['afsec']>0:
                Timer(ctrigger['afsec'], do_trigger_followup, [aename]).start()
                print(f"set trigger followup in {ctrigger['afsec']} sec")
            else:
                print(f"invalid afsec= {ctrigger['afsec']}")



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

    #samplerate에 따라 파일에 저장되는 data 조정
    #현재 가속도 센서에만 적용중
    for aename in ae:
        ae_samplerate = int(ae[aename]["config"]["cmeasure"]["samplerate"])
        # acceleration의 경우, samplerate가 100이 아닌 경우에 대처한다
        if sensor_type(aename)=="AC" and ae_samplerate != 100:
            if 100%ae_samplerate != 0 : #100의 약수가 아닌 samplerate가 설정되어있는 경우, 오류가 발생한다
                print("wrong samplerate config")
                print("apply standard samplerate = 100")
                ae_samplerate = 100
            new_acc_list = list()
            merged_value = 0
            merge_count = 0
            sample_number = 100//ae_samplerate
            for i in range(len(acc_list)):
                merged_value += acc_list[i]
                merge_count += 1
                if merge_count == sample_number:
                    new_acc_list.append(round(merged_value/sample_number, 2))
                    merge_count = 0
            acc_list = new_acc_list
            #print("samplerate calculation end")
            #print(acc_list)
        

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
    # 내 device의 ae에 지정된 sensor type 정보만을 전송
    for aename in ae:
        # stype 은 'AC' 와 같은 부분
        stype = sensor_type(aename)
        #print(f"mqtt {aename} {stype} {ae[aename]['local']['realstart']}")
        if ae[aename]['local']['realstart']=='Y':  # mqtt_realtime is controlled from remote user
            if stype=='AC': payload = Acceleration_json["data"]
            elif stype=='TI': payload = Degree_json["data"]
            elif stype=='TP': payload = Temperature_json["data"]
            elif stype=='DI': payload = Displacement_json["data"]

            #print(F'real mqtt /{cse["name"]}/{aename}/realtime')
            mqtt_sending(aename, payload)

    
    # 센서별 json file 생성
    # 내 ae에 지정된 sensor type정보만을 저장
    for aename in ae:
        stype = sensor_type(aename)
        if stype=='TI': jsonSave(deg_path, Degree_json)
        elif stype=='TP': jsonSave(tem_path, Temperature_json)
        elif stype=='DI': jsonSave(dis_path, Displacement_json)
        elif stype=='AC': jsonSave(acc_path, Acceleration_json)

    #print(f'CAPTURE {now.strftime("%H:%M:%S:%f")} capture,process={(t2_start-t1_start)*1000:.1f}+{(process_time()-t2_start)*1000:.1f}ms got {len(rData)}B {rData[:50]} ...')

def do_measure_report():
    global ae
    for aename in ae: 
        if sensor_type(aename)=='AC': periodic_acceleration.report()
        elif sensor_type(aename)=='TP': periodic_temperature.report()
        elif sensor_type(aename)=='DI': periodic_displacement.report()
        elif sensor_type(aename)=='TI': periodic_degree.report()
        else:
            print('PANIC: unsupported sensor type')

gotnewfile=False
for aename in ae:
    if not ae[aename]["info"]["manufacture"]["fwver"] == VERSION:
        print(f'fwver {ae[aename]["info"]["manufacture"]["fwver"]} != {VERSION}  create save file.')
        ae[aename]["info"]["manufacture"]["fwver"]=VERSION
        gotnewfile=True
if gotnewfile:
    save_conf()
	
for aename in ae:
    cmeasure=ae[aename]['config']['cmeasure']
    if 'stateperiod' in cmeasure and str(cmeasure['stateperiod']).isnumeric():
        interval = cmeasure['stateperiod']
    else:
        interval = 60  #min
    RepeatedTimer(interval*60, periodic_state.report)

    if 'measureperiod' in cmeasure and str(cmeasure['measureperiod']).isnumeric():
        interval = cmeasure['measureperiod']
    else:
        interval = 600  #sec
    RepeatedTimer(interval, do_measure_report)

    if 'rawperiod' in cmeasure and str(cmeasure['rawperiod']).isnumeric():
        interval = cmeasure['rawperiod']
    else:
        interval = 60  #min
    print(f"cmeasure.measureperiod= {cmeasure['measureperiod']} sec") 
    print(f"cmeasure.stateperiod= {cmeasure['stateperiod']} min") 
    print(f"cmeasure.rawperiod= {cmeasure['rawperiod']} min") 
    print(f"cmeasure.usefft= {cmeasure['usefft']}") 
    print(f"ctrigger.use= {ae[aename]['config']['ctrigger']['use']}") 
    # rawperiod의 간격마다 raw file 통합 실시
    # 아직 실제 raw file 전송은 수행하고 있지 않음
    # for test, rawperiod is 10 seconds
    RepeatedTimer(interval*60, File_Merge.doit)
    RepeatedTimer(interval*60, File_Cleaner.doit)

    print('create ci at boot')
    create.allci(aename, {'config','info'})
    print('Ready')
    do_config(aename, 'nosave')


# every 1.0 sec
RepeatedTimer(1.0, do_capture)
