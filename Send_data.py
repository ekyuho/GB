# Send_data.py
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

trigger_in_progress={}

last_sensor_value={}

#센서별 데이타 저장소, 디렉토리가 없으면 자동생성
acc_path = F"{root}/raw_data/Acceleration"
deg_path = F"{root}/raw_data/Degree"
dis_path = F"{root}/raw_data/Displacement"
str_path = F"{root}/raw_data/Strain"
tem_path = F"{root}/raw_data/Temperature"


def sensor_type(aename):
    return aename.split('-')[1][0:2]

# handles periodic measure (fft for AC)
def do_periodic_data():
    global ae, mytimer
    for aename in ae: 
        if mytimer.ring(aename, 'data'):
            if ae[aename]['local']['measurestart']=='N':  # measure is controlled from remote user
                print('measurestart==N, skip periodic data sending')
                continue

            print(f'periodic_data: time to run')
            stype = sensor_type(aename)
            print(f'do_measure {aename}')
            if stype=='AC': 
                periodic_acceleration.report(aename)
            elif stype=='DI':
                periodic_displacement.report(aename)
            elif stype=='TI':
                periodic_degree.report(aename)
            elif stype=='TP':
                periodic_temperature.report(aename)
	
def tick1sec():
    global mytimer
    mytimer.update()
    if True or ae[aename]['local']['printtick']=='Y': mytimer.current()
    do_periodic_data() # create ci at given interval

for aename in ae:
    cmeasure=ae[aename]['config']['cmeasure']

    if 'measureperiod' in cmeasure and isinstance(cmeasure['measureperiod'],int): 
        mytimer.set(aename, 'data', cmeasure['measureperiod'])
        print(f"cmeasure.measureperiod= {cmeasure['measureperiod']} sec") 
    else: 
        mytimer.set(aename, 'data', 600)  #default sec
        print(f"cmeasure.measureperiod= defaulted 600 sec") 

    print(f"cmeasure.usefft= {cmeasure['usefft']}") 
    print(f"ctrigger.use= {ae[aename]['config']['ctrigger']['use']}") 


print('Ready')
# every 1.0 sec
RepeatedTimer(1, tick1sec)
