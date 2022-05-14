# Client_Data_Saving.py
# date : 2022-04-28
# 작성자 : ino-on, 주수아
# 소켓 서버로 'CAPTURE' 명령어를 1초에 1번 보내, 센서 데이터값을 받습니다.
# 받은 데이터를 센서 별로 분리해 각각 다른 디렉토리에 저장합니다.
# 현재 mqtt 전송도 이 프로그램에서 담당하고 있습니다.
VERSION='2.0'
print('\n===========')
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
import re
from time import process_time
from datetime import datetime, timedelta
from paho.mqtt import client as mqtt
from events import Events
from RepeatedTimer import RepeatedTimer
import MyTimer
mytimer= MyTimer.MyTimer()

import versionup
import periodic_state
import periodic_acceleration
import periodic_temperature
import periodic_degree
import periodic_displacement
import create  #for Mobius resource
import conf

import make_oneM2M_resource

import File_Merge
import File_Cleaner

broker = conf.host
port = conf.port
cse = conf.cse
ae = conf.ae

root=conf.root
worktodo=""
worktodo_param={}

TOPIC_callback=f'/oneM2M/req/{cse["name"]}/#'
TOPIC_response=f'/oneM2M/resp/{cse["name"]}'
TOPIC_list = conf.TOPIC_list
mqttc=""
command=""
# key==aename
trigger_in_progress={}


last_sensor_value={}

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

client_socket=""

def connect():
    global client_socket
    if client_socket=="":
        client_socket= socket(AF_INET, SOCK_STREAM)
        client_socket.settimeout(5)
        try:
            client_socket.connect(('127.0.0.1', 50000))
        except:
            print('got no connection')
            return 'no'
        print("socket 연결에 성공했습니다.")
    return "yes"

if connect()=='no':
    sys.exit(1)

make_oneM2M_resource.makeit()
print('done any necessary Mobius resource creation')

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
    global ae, worktodo, worktodo_param
    global mytimer
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
    elif cmd in {'settrigger'}:
        print(f'set ctrigger= {jcmd["ctrigger"]}')
        for x in jcmd["ctrigger"]:
            ae[aename]["config"]["ctrigger"][x]= jcmd["ctrigger"][x]

        #do_config(aename)
        worktodo = do_config
        worktodo_param={"aename":aename, "save":'save', "cmd":cmd}
    elif cmd in {'setmeasure'}:
        print(f'set cmeasure= {jcmd["cmeasure"]}')
        for x in jcmd["cmeasure"]:
            ae[aename]["config"]["cmeasure"][x]= jcmd["cmeasure"][x]
        if "measureperiod" in jcmd["cmeasure"]: mytimer.set(aename, 'data', cmeasure['measureperiod'])
        if "stateperiod" in jcmd["cmeasure"]: mytimer.set(aename, 'state', cmeasure['stateperiod'])
        if "rawperiod" in jcmd["cmeasure"]: mytimer.set(aename, 'file', cmeasure['rawperiod'])
        save_conf()
    elif cmd in {'settime'}:
        print(f'set time= {jcmd["time"]}')
        ae[aename]["config"]["time"]= jcmd["time"]
        save_conf()
    elif cmd in {'setconnect'}:
        print(f'set {aename}/connect= {jcmd["connect"]}')
        for x in jcmd["connect"]:
            ae[aename]["connect"][x]=jcmd["connect"][x]
        create.ci(targetae, 'config', 'connect')
        save_conf()
    elif cmd in {'measurestart'}:
        print('start regular measure tx')
        mqtt_measure=True
    elif cmd in {'measurestop'}:
        print('stop regular measure tx')
        mqtt_measure=False
    elif cmd == 'inoon':
        print(f'cmd onoon {jcmd["cmd2"]}')
        if jcmd["cmd2"] == 'data': mytimer.expired[aename]['data']= True  # run at the beginning
        if jcmd["cmd2"] == 'file': mytimer.expired[aename]['file']= True  # run at the beginning
        if jcmd["cmd2"] == 'state': mytimer.expired[aename]['state']= True  # run at the beginning
        
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
        #print(' ==> not for me', topic, msg[:20],'...')
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
    


time_old=datetime.now()

def do_config(param):
    global client_socket
    global ae

    aename=param["aename"]
    cmd=param["cmd"]
    save=param["save"]

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

    if connect() == 'no': 
        return
    try:
        client_socket.sendall(("CONFIG"+json.dumps(setting, ensure_ascii=False)).encode())
        rData = client_socket.recv(10000)
    except OSError as msg:
        print(f"socket error {msg} exiting..")
        os._exit(0)


    rData = rData.decode('utf_8')
    jsonData = json.loads(rData) # jsonData : 서버로부터 받은 json file을 dict 형식으로 변환한 것

    if jsonData["Status"] == "False":
        ae[aename]["state"]["abflag"]="Y"
        ae[aename]["state"]["abtime"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ae[aename]["state"]["abdesc"]="board config failed"
        create.ci(aename, 'state','')
        return


    if save=='save':
        print(f'do_config: got result {jsonData}')
        if cmd in {'ctrigger', 'cmeasure'}:
            create.ci(targetae, 'config', cmd)
        elif cmd == 'settime':
            create.ci(targetae, 'config', 'time')
        save_conf()

def do_trigger_followup(aename):
    global ae
    print(f'trigger_followup {aename}')
    trigger_in_progress[aename]=0
    dtrigger=ae[aename]['data']['dtrigger']

    def find_pathlist():
        global ae
        ctrigger = ae[aename]['config']['ctrigger']
        path = F"{root}/raw_data/Acceleration"
        file_list = os.listdir(path)
        present_time = time.time()
        data_path_list = list()
        for i in range (len(file_list)):
            file_time = os.path.getmtime(path+'/'+file_list[i])
            time_gap = present_time-file_time
            if time_gap <= ctrigger['afsec']+ctrigger['bfsec']: # 데이터 생성시각을 기준으로 데이터 수집중. 
                data_path_list.append(path+'/'+file_list[i])
                #print(file_list[i])
        data_path_list.sort()
        return data_path_list

    # path에 존재하는 모든 data를 열어보고, 보낼 데이터 list를 작성한다.
    # 정렬된 data_path_list가 들어오기 때문에, 가장 처음 들어오는 데이터가 가장 오래된 데이터. 즉, start data이다.
    def merge_data(data_path_list):
        global ae
        dtrigger=ae[aename]['data']['dtrigger']
        data_list = list()
        for file in range(len(data_path_list)):
            with open(data_path_list[file], "rb") as f:
                one_file = json.loads(f.read().decode('utf_8'))
                if file==0:
                    dtrigger["start"] = one_file["time"]
            for i in range(len(one_file["data"])):
                data_list.append(one_file["data"][i])

        return data_list
    #아래의  function을 만들어야 합니다
    
    data = merge_data(find_pathlist())
    #data= merge_data(dtrigger['start'])
    #data=[1,2,3,4,5]

    dtrigger['count']=len(data)
    dtrigger['data']=data
    create.ci(aename, 'data', 'dtrigger')
    print("trigger data has sent")


def do_capture():
    global client_socket, mqtt_measure, time_old
    global worktodo, worktodo_param
    global ae #samplerate 조정을 위한 값. 동적 데이터에만 적용되는 것으로 한다

    if not worktodo=="":
        print('call work to do')
        worktodo(worktodo_param)
        worktodo=""
        return

    t1_start=process_time()
    #print('do capture')
    if connect() == 'no':
        return
    try:
        client_socket.sendall("CAPTURE".encode()) # deice server로 'CAPTURE' 명령어를 송신합니다.
        rData = client_socket.recv(10000)
    except OSError as msg:
        print(f"socket error {msg} exiting..")
        os._exit(0)

    t2_start=process_time()
    rData = rData.decode('utf_8')
    try:
        jsonData = json.loads(rData) # jsonData : 서버로부터 받은 json file을 dict 형식으로 변환한 것
    except ValueError:
        print("socket troubled. exiting.")
        sys.exit(1)
    now=datetime.now()

    if jsonData["Status"] == "False":
        print(f' ** no data {now.strftime("%H:%M:%S")} +{(now-time_old).total_seconds():.1f} sec')
        time_old=now
        return
    
    #print('got=',jsonData)
    j=jsonData
    for aename in ae:
        if 'trigger' in j and sensor_type(aename) in j['trigger'] and j['trigger'][sensor_type(aename)]=='1':
            if aename in trigger_in_progress and trigger_in_progress[aename]==1:
                continue

            if sensor_type(aename) == "AC": # 동적 데이터의 경우, 트리거 전초와 후초를 고려해 전송 시행
                    
                trigger_in_progress[aename]=1
                ctrigger=ae[aename]['config']['ctrigger']
                cmeasure=ae[aename]['config']['cmeasure']
                dtrigger=ae[aename]['data']['dtrigger']
                dtrigger['time']=jsonData["Timestamp"] # 트리거 신호가 발생한 당시의 시각
                dtrigger['start']=(now-timedelta(seconds=ctrigger['bfsec'])).strftime("%Y-%m-%d %H:%M:%S.%f") #[트리거 발생 당시 시각 - bfsec]의 시각
                dtrigger['mode']=ctrigger['mode']
                dtrigger['sthigh']=ctrigger['st1high']
                dtrigger['stlow']=ctrigger['st1low']
                dtrigger['samplerate']=cmeasure['samplerate']
                #dtrigger['val']=1

                print(f"got trigger {aename} bfsec= {ctrigger['bfsec']}  afsec= {ctrigger['afsec']}")
                if int(ctrigger['afsec']) and ctrigger['afsec']>0:
                    Timer(ctrigger['afsec'], do_trigger_followup, [aename]).start()
                    print(f"set trigger followup in {ctrigger['afsec']} sec")
                else:
                    print(f"invalid afsec= {ctrigger['afsec']}")
            
            else: # 정적 데이터의 경우, 트리거 발생 당시의 데이터를 전송한다

                ctrigger=ae[aename]['config']['ctrigger']
                cmeasure=ae[aename]['config']['cmeasure']
                dtrigger=ae[aename]['data']['dtrigger']
                dtrigger['time']=jsonData["Timestamp"] # 트리거 신호가 발생한 당시의 시각
                dtrigger['start']=jsonData["Timestamp"]
                dtrigger['mode']=ctrigger['mode']
                dtrigger['sthigh']=ctrigger['st1high']
                dtrigger['stlow']=ctrigger['st1low']
                dtrigger['samplerate']=cmeasure['samplerate']
                dtrigger['count'] = 1

                data_list = list()
                
                

                if sensor_type(aename) == "DI":
                    data_list.append(jsonData["Displacement"][dis_channel])
                elif sensor_type(aename) == "TP":
                    data_list.append(jsonData["Temperature"])
                elif sensor_type(aename) == "TI":
                    data_list.append(jsonData["Degree"][deg_axis])
                else:
                    data_list.append("nope")

                dtrigger['data'] = data_list
                print(f"got trigger {aename}")
                print("trigger data uploading...")
                create.ci(aename, "data", "dtrigger") # 정적 트리거 전송은 따로 do_trigger_followup을 실행하지 않는다.
                print("trigger data has sent")
                


    time_old=now
    if not "Timestamp" in jsonData:
        print(f'****** no Timestamp  {jsonData}')
        return

    Time_data = jsonData["Timestamp"]
    Temperature_data = jsonData["Temperature"]
    Displacement_data = jsonData["Displacement"][dis_channel]
    
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
        if not aename in last_sensor_value: last_sensor_value[aename]={}
        if stype=='AC': 
            jsonSave(acc_path, Acceleration_json)
            last_sensor_value[aename][stype]=Acceleration_json
        elif stype=='TI': 
            jsonSave(deg_path, Degree_json)
            last_sensor_value[aename][stype]=Degree_json
        elif stype=='TP': 
            jsonSave(tem_path, Temperature_json)
            last_sensor_value[aename][stype]=Temperature_json
        elif stype=='DI': 
            jsonSave(dis_path, Displacement_json)
            last_sensor_value[aename][stype]=Displacement_json


    #print(f'CAPTURE {now.strftime("%H:%M:%S:%f")} capture,process={(t2_start-t1_start)*1000:.1f}+{(process_time()-t2_start)*1000:.1f}ms got {len(rData)}B {rData[:50]} ...')

# handles periodic measure (fft for AC)
def do_periodic_data():
    global ae, mytimer
    for aename in ae: 
        if mytimer.ring(aename, 'data'):
            print(f'periodic_data: got expiration')
            if not aename in last_sensor_value:
                print('do_periodic_data: no data, skip')
                continue

            stype = sensor_type(aename)
            if not stype in last_sensor_value[aename]:
                print(f'do_periodic_data: PANIC {aename} {last_sensor_value[aename]}')
                return
            print(f'do_measure {aename}')
            if stype=='AC': 
                periodic_acceleration.report(aename)
            else:
                dmeasure = {}
                dmeasure['val'] = last_sensor_value[aename][stype]
                ae[aename]['data']['dmeasure'] = dmeasure
                create.ci(aename, 'data', 'dmeasure')

def do_periodic_state():
    global ae, mytimer
    for aename in ae: 
        if mytimer.ring(aename, 'state'):
            print(f'periodic_state: got expiration')
            create.ci(aename, 'state','')

def do_periodic_file():
    global ae, mytimer
    for aename in ae: 
        if mytimer.ring(aename, 'file'):
            print(f'periodic_file: got expiration')
            File_Merge.doit
            File_Cleaner.doit
	
def tick1sec():
    global mytimer
    mytimer.update()
    #mytimer.current()
    #print('tick()')
    do_capture() # fetch sensor from board
    do_periodic_data() # create ci at given interval
    do_periodic_state() # state create ci at given interval
    do_periodic_file()  # http upload at given interval


def startup():
    global ae
    print('create ci at boot')
    for aename in ae:
        create.allci(aename, {'config','info'})
        do_config({'aename':aename, 'cmd':'','save':'nosave'})
        mytimer.timer[aename]['data']= 3  # run at the beginning


for aename in ae:
    cmeasure=ae[aename]['config']['cmeasure']
    print(f"cmeasure['stateperiod'] ={cmeasure['stateperiod']}")
    if 'stateperiod' in cmeasure and isinstance(cmeasure['stateperiod'],int): 
        mytimer.set(aename, 'state', cmeasure['stateperiod'])
        print(f"cmeasure.stateperiod= {cmeasure['stateperiod']} min")
    else: 
        mytimer.set(aename, 'state', 60*60)  #default min
        print(f"cmeasure.stateperiod= defaulted 60 min")

    if 'measureperiod' in cmeasure and isinstance(cmeasure['measureperiod'],int): 
        mytimer.set(aename, 'data', cmeasure['measureperiod'])
        print(f"cmeasure.measureperiod= {cmeasure['measureperiod']} sec") 
    else: 
        mytimer.set(aename, 'data', 600)  #default sec
        print(f"cmeasure.measureperiod= defaulted 600 sec") 

    if 'rawperiod' in cmeasure and isinstance(cmeasure['rawperiod'],int): 
        mytimer.set(aename, 'file', cmeasure['rawperiod'])
        print(f"cmeasure.rawperiod= {cmeasure['rawperiod']} min") 
    else: 
        mytimer.set(aename, 'file', 60*60)  #default min
        print(f"cmeasure.rawperiod= defauled 60 min") 

    print(f"cmeasure.usefft= {cmeasure['usefft']}") 
    print(f"ctrigger.use= {ae[aename]['config']['ctrigger']['use']}") 


print('Ready')
Timer(10, startup).start()
# every 1.0 sec
RepeatedTimer(1.0, tick1sec)
