# Client_Data_Saving.py
# 소켓 서버로 'CAPTURE' 명령어를 1초에 1번 보내, 센서 데이터값을 받습니다.
# 받은 데이터를 센서 별로 분리해 각각 다른 디렉토리에 저장합니다.
# 현재 mqtt 전송도 이 프로그램에서 담당하고 있습니다.
VERSION='2-2_20220519_1755'
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

broker = conf.host
port = conf.port
cse = conf.cse
ae = conf.ae
root=conf.root

#센서별 데이타 저장소, 디렉토리가 없으면 자동생성
acc_path = F"{root}/raw_data/Acceleration"
deg_path = F"{root}/raw_data/Degree"
dis_path = F"{root}/raw_data/Displacement"
str_path = F"{root}/raw_data/Strain"
tem_path = F"{root}/raw_data/Temperature"

def do_periodic_state():
    global ae, mytimer
    if mytimer.ring(aename, 'state'):
        print(f'periodic_state: time to run')
        periodic_state.report()

def tick1sec():
    global mytimer
    mytimer.update()
    if True or ae[aename]['local']['printtick']=='Y': mytimer.current()
    do_periodic_state() # state create ci at given interval


for aename in ae:
    cmeasure=ae[aename]['config']['cmeasure']
    print(f"cmeasure['stateperiod'] ={cmeasure['stateperiod']}")
    if 'stateperiod' in cmeasure and isinstance(cmeasure['stateperiod'],int): 
        mytimer.set(aename, 'state', cmeasure['stateperiod'])
        print(f"cmeasure.stateperiod= {cmeasure['stateperiod']} min")
    else: 
        mytimer.set(aename, 'state', 60*60)  #default min
        print(f"cmeasure.stateperiod= defaulted 60 min")

    print(f"cmeasure.usefft= {cmeasure['usefft']}") 
    print(f"ctrigger.use= {ae[aename]['config']['ctrigger']['use']}") 



print('Ready')
# every 1.0 sec
RepeatedTimer(1, tick1sec)
