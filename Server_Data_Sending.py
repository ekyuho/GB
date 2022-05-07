# Server_Data_Sending.py
# date : 2022-05-06
# 초기 작성자 : ino-on, 주수아
# 소켓 클라이언트와 통신을 하며, 클라이언트가 명령어를 보낼 때마다 명령어에 따른 동작을 수행합니다.
# 현재 'CAPTURE' 명령어만이 활성화되어있습니다. 

#   5/6 변위식 수정. 추후 인하대쪽 코드와 통합할 예정입니다, 주수아
#   5/5 making robust를 위한 작업들, 김규호 

import spidev
import time
import numpy as np
import socket
import select
import json
import math
from datetime import datetime
import re

import conf
cse = conf.cse
ae = conf.ae


spi_bus = 0
spi_device = 0
spi = spidev.SpiDev()
spi.open(spi_bus, spi_device)
spi.max_speed_hz = 100000 #100MHz

console_msg=""

rq_cmd = [0x01]*6
CMD_A = [0x10]*6
CMD_B = [0x20]*6


def request_cmd() :
    RXD = spi.xfer2(rq_cmd)
    print(RXD)
    if   RXD == [0x2, 0x3, 0x4, 0x5, 0x6, 0x7] : # ACK
        return 1
    else : 
        return 0

def send_data(cmd) : 
    RXD = spi.xfer3(cmd)
    print(RXD)
    return RXD

def time_conversion(stamp):
    global BaseTimeStamp
    global BaseTime
    #t_delta = BaseTimeStamp - stamp    

    #t_delta = stamp- BaseTimeStamp     
    #return str(BaseTime + timedelta(milliseconds = t_delta))

    c_delta = stamp - BaseTimeStamp
    return str(BaseTime + timedelta(milliseconds = c_delta))


def sync_time():
    global BaseTime
    global BaseTimeStamp
    
    BaseTime = datetime.now()
    time.sleep(ds)  
    spi.xfer2([0x27])
    time.sleep(ds)  
    status_data_i_got = spi.xfer2([0x0]*14)

    BaseTimeStamp = status_data_i_got[3] << 24 | status_data_i_got[2] << 16 | status_data_i_got[1] << 8 | status_data_i_got[0]  - TimeCorrection

# int Twos_Complement(string data, int length)
# bit data를 int data로 바꾸어줍니다.
# first bit가 1이라면 보수 연산을 시행하며, 그렇지 않으면 보수 연산을 시행하지 않습니다.
def Twos_Complement(data, length):
    def convert(data):
        uintval = int(data, 16)
        bit = 4 * (len(data) - 2)
        if uintval >= math.pow(2,bit-1):
            uintval = int(0 - (math.pow(2, bit)-uintval))
        return uintval
    int_data = int(data, 16)
    bin_data = bin(int_data)
    if len(bin_data) == length*8+2:
        return convert('0x'+data)
    else:
        return int_data
    
    
# int basic_conversion(list number_list)
# convert whole bit data to demical
# if first bit is '1', it calculates minus value according to Two's Complement
# 현재 큰 의미 없는 코드
def basic_conversion(number_list):
    result_str = ''
    for i in range(len(number_list)):
        result_hex = hex(number_list[i])[2:]
        result_str += result_hex
    result = int(result_str, 16)
    result = -(result & 0x80000000) | (result & 0x7fffffff)
    return result

# int dis_conversion(list number_list)
# convert whole displacement bit data to demical
# if first bit is '1', it calculates minus value according to Two's Complement
def dis_conversion(number_list):
    result_str = ''
    for i in reversed(range(len(number_list))):
        result_hex = hex(number_list[i])[2:]
        if len(result_hex)<2:
            result_hex = '0'+result_hex
        result_str += result_hex
    result = Twos_Complement(result_str, 4)
    result = (result-16339000)/699.6956*(1.01)
    return result

# float acc_conversion(list number_list)
# convert whole acceleration bit data to acc data
# if first bit is '1', it calculates minus value according to Two's Complement
def acc_conversion(number_list):
    result_str = ''
    for i in reversed(range(len(number_list))):
        result_hex = hex(number_list[i])[2:]
        if len(result_hex)<2:
            result_hex = '0'+result_hex
        result_str += result_hex
    result_int = Twos_Complement(result_str, 4)
    result = float(result_int)
    result *= 0.0039
    result = round(result, 2)
    return result

# float deg_conversion(list number_list)
# convert whole degree bit data to deg data
# if first bit is '1', it calculates minus value according to Two's Complement
def deg_conversion(number_list):
    result_str = ''
    for i in reversed(range(len(number_list))):
        result_hex = hex(number_list[i])[2:]
        if len(result_hex)<2:
            result_hex = '0'+result_hex
        result_str += result_hex
    result_int = Twos_Complement(result_str, 2)
    result = float(result_int)
    result /= 100
    return result

# float tem_conversion(list number_list)
# convert whole temperature bit data to tem data
# if first bit is '1', it calculates minus value according to Two's Complement
def tem_conversion(number_list):
    result_str = ''
    for i in reversed(range(len(number_list))):
        result_hex = hex(number_list[i])[2:]
        if len(result_hex)<2:
            result_hex = '0'+result_hex
        result_str += result_hex
    #result_str = result_str[::-1] # invert string
    result_int = Twos_Complement(result_str, 2)
    result = float(result_int)
    result /= 100
    return result

# 220506 갱신 : 변위 변환 수식 수정 완료


i =0
d = 1
ds = 0.01
d2 = 0.1
n = 2400
BaseTime = datetime.now()   # basetime , 처음 동작할 때 다시 초기화함

BaseTimeStamp = 0
TimeCorrection = int(ds * 1000) # FIXME

isReady = False

upload_HEADER = ["Timestamp", "Temperature", "Displacement"]
capture_HEADER = ["Timestamp", "Temperature", "Displacement", "samplerate"]
ctrigger_CONFIG = ["use", "mode", "st1high", "st1low", "bfsec"]
cmeasure_CONFIG = ["sensitivity", "samplerate", "measureperiod", "stateperiod", "rawperiod"]
STATUS = ["ibattery", "ebattery", "count", "abflag", "abtime", "abdesc"]
num_of_DATA = 2

# dict data_receiving()
# 센서로부터 data bit를 받아, 그것을 적절한 int값으로 변환합니다.
# return value는 모든 센서 데이터를 포함하고 있는 dictionary 데이터입니다.
def data_receiving():
    global console_msg
    #print("s:0x24")		# request header
    rcv1 = spi.xfer2([0x24])
    #print("header data signal")
    time.sleep(ds)

    #print("s:0x40")
    rcv2 = spi.xfer2([0x40]*8) # follow up action
    time.sleep(ds)
    #print(rcv2)
    #print(F"got {len(rcv2)}B {rcv2[0:20]}...")
    
    if rcv2[0] == 216 and rcv2[1] == 216:
        isReady = True
        json_data = {}
        #print("data is ready")
        status = basic_conversion(rcv2[2:4]) #status info save
        timestamp = basic_conversion(rcv2[4:8]) #timestamp info save. 현재 유효한 timestamp 연산을 하고 있지 않습니다.
        json_data["Timestamp"] = timestamp
        json_data["Status"] = status
    else:
        isReady = False
        console_msg += " ** device not ready"
        fail_data = {"Status":"False"}
        return fail_data
        
    if isReady: #only send data if data is ready
        #print("s:"+ "0x26")		# request static
        rcv3 = spi.xfer2([0x26])
        #print(rcv3)
        #print("static sensor data signal")
        time.sleep(ds)

        #print("s:"+ "0x40")
        rcv4 = spi.xfer2([0x40]*16) # follow up action
        #print(rcv4)
        degreeX = deg_conversion(rcv4[0:2])
        degreeY = deg_conversion(rcv4[2:4])
        degreeZ = deg_conversion(rcv4[4:6])
        Temperature = tem_conversion(rcv4[6:8])
        Displacement_ch4 = dis_conversion(rcv4[8:12])
        Displacement_ch5 = basic_conversion(rcv4[12:])

        json_data["Degree"] = {"x":degreeX, "y":degreeY, "z":degreeZ}
        json_data["Temperature"] = Temperature
        json_data["Displacement"] = {"ch4":Displacement_ch4, "ch5":Displacement_ch5}
        time.sleep(ds)
 
        #print("s:"+ "0x25")        # request data	
        rcv5 = spi.xfer2([0x25])
        #print(rcv5)
        #print("Dynamic sensor data signal")
        time.sleep(ds)

        #print("s:"+ "0x40")
        rcv6 = spi.xfer2([0x40]*n)
        #print(rcv6)
        acc_list = list()
        strain_list = list()
        for i in range(100):
            cycle = i*24
            ax = acc_conversion(rcv6[0+cycle:4+cycle])
            ay = acc_conversion(rcv6[4+cycle:8+cycle])
            az = acc_conversion(rcv6[8+cycle:12+cycle])
            acc_list.append({"x":ax, "y":ay, "z":az})
            #acc_list.append([ax, ay, az])
            sx = basic_conversion(rcv6[12+cycle:16+cycle])
            sy = basic_conversion(rcv6[16+cycle:20+cycle])
            sz = basic_conversion(rcv6[20+cycle:24+cycle])
            strain_list.append({"x":sx, "y":sy, "z":sz})
            #strain_list.append([sx, sy, sz])

        json_data["Acceleration"] = acc_list
        json_data["Strain"] = strain_list
        time.sleep(d2)
        j=json.dumps(json_data)
        console_msg += F" {len(j)}B {j[0:60]} ..."
        return json_data

def set_config_data(config_data):
    temp_config = json.loads(config_data)
    results = {} 
    ttp = tdp = tti = tac = 0

    global Offset
    # set offset
    # config_data  는 하나의  AE 즉 하나의 센서에 대한 설정값인데, AC, DI, TI, TP 4개를 다 처리??
    # 어차피  function  내에서 사용하지 않음
    #Offset['ac'] =  temp_config['cmeasure-ac']['offset']  
    #Offset['di'] = temp_config['cmeasure-di']['offset']  
    #Offset['ti'] = temp_config['cmeasure-ti']['offset']  
    #Offset['tp'] = temp_config['cmeasure-tp']['offset']  
    ####XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    
    # making triger_seltect
    #if temp_config['ctrigger-tp']['use'] == 'Y':
    #    ttp = int(0x1000)

    #if temp_config['ctrigger-di']['use'] == 'Y':
    #    tdp = int(0x0800)

    #if temp_config['ctrigger-ti']['use'] == 'Y':
    #    tti = int(0x0200)

    #if temp_config['ctrigger-ac']['use'] == 'Y':
    #    tac = int(0x0100)
    ####XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    
    # formatting for GBC data structure and tranmisssion (two bytes) 
    # Revise latter!!!
    results['samplingRate'] = 100       # hw fix 5/9
    results['sensingDuration_l'] = 204  # fix 5/9, 432,000,000 = 19bfcc00 -> 00cc bf19
    results['sensignDuration_h'] = 48921     # fix 5/9
    results['measurePeriod'] = 600       # hw fix 5/9 

    chval = 6
    if ((chval < 256) and (chval>0)): 
        results['dummy4'] = 0
    results['uploadPeriod'] = chval       # hw fix 5/9
    
    chval = ttp|tdp|tti|tac
    if ((chval < 256) and (chval>0)): 
        results['dummy5'] = 0

    
    # making triger_seltect
    #if temp_config['ctrigger-tp']['use'] == 'Y':
        #ttp = int(0x1000)

    #if temp_config['ctrigger-di']['use'] == 'Y':
        #tdp = int(0x0800)

    #if temp_config['ctrigger-ti']['use'] == 'Y':
        #tti = int(0x0200)

    #if temp_config['ctrigger-ac']['use'] == 'Y':
        #tac = int(0x0100)
    ####XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    
    # formatting for GBC data structure and tranmisssion (two bytes) 
    # Revise latter!!!
    results['samplingRate'] = 100       # hw fix 5/9
    results['sensingDuration_l'] = 204  # fix 5/9, 432,000,000 = 19bfcc00 -> 00cc bf19
    results['sensignDuration_h'] = 48921     # fix 5/9
    results['measurePeriod'] = 600       # hw fix 5/9 

    chval = 6
    if ((chval < 256) and (chval>0)): 
        results['dummy4'] = 0
    results['uploadPeriod'] = chval       # hw fix 5/9
    
    chval = ttp|tdp|tti|tac
    if ((chval < 256) and (chval>0)): 
        results['dummy5'] = 0
    results['sensorSelect'] = chval   

    '''
    chval = int(tohex1( int(temp_config['ctrigger-tp']['st1high']*100), 16),16)
    if ((chval < 256) and (chval>0)): 
        results['dummy6'] = 0
    results['highTemp'] = chval      
    
    chval = int(tohex1( int(temp_config['ctrigger-tp']['st1low']*100), 16),16)
    if ((chval < 256) and (chval>0)): 
        results['dummy7'] = 0
    results['lowTemp'] = chval      
    
    chval = int(tohex1( int(temp_config['ctrigger-di']['st1high']*100), 16),16)
    if ((chval < 256) and (chval>0)): 
        results['dummy8'] = 0
    results['highDisp'] = chval      

    chval = int(tohex1( int(temp_config['ctrigger-di']['st1low']*100), 16),16)
    if ((chval < 256) and (chval>0)): 
        results['dummy9'] = 0
    results['lowDisp'] = chval      
    '''

    chval = 0 
    if ((chval < 256) and (chval>0)): 
        results['dummy10'] = 0
    results['highStrain'] = chval       
    
    chval = 0 
    if ((chval < 256) and (chval>0)): 
        results['dummy11'] = 0
    results['lowStrain'] = chval    

    '''
    chval = int(tohex1( int(temp_config['ctrigger-ti']['st1high']*100), 16),16)
    if ((chval < 256) and (chval>0)): 
        results['dummy12'] = 0
    results['higTilt'] = chval   

    chval = int(tohex1( int(temp_config['ctrigger-ti']['st1low']*100), 16),16)
    if ((chval < 256) and (chval>0)): 
        results['dummy13'] = 0
    results['lowTilt'] = chval   

    chval = int(tohex1( int(temp_config['ctrigger-ac']['st1high']/0.0039), 16),16)
    if ((chval < 256) and (chval>0)): 
        results['dummy14'] = 0
    results['highAcc'] = chval       # hw fix 5/9

    chval = int(tohex1( int(temp_config['ctrigger-ac']['st1low']/0.0039), 16),16)
    if ((chval < 256) and (chval>0)): 
        results['dummy15'] = 0
    results['lowAcc'] = chval       # hw fix 5/9
    '''

    # end of formatting 
    
    return results 



def get_status_data():
    global BaseTime
    
    spi.xfer2([0x27])
    time.sleep(ds)
    status_data_i_got = spi.xfer2([0x0]*14)

    timestamp   = status_data_i_got[3]  << 24 | status_data_i_got[2] << 16 | status_data_i_got[1] << 8 | status_data_i_got[0] - TimeCorrection
    solar   = status_data_i_got[7]  << 8  | status_data_i_got[6]  
    battery  = status_data_i_got[9]  << 8  | status_data_i_got[8]   
    vdd     = status_data_i_got[11] << 8  | status_data_i_got[10]  

    solar, battery, vdd = status_conversion(solar, battery, vdd)

    status_data={}
    status_data["timestamp"] = time_conversion( timestamp ) # board uptime 
    status_data["resetFlag"] = status_data_i_got[5]  << 8  | status_data_i_got[4]   
    status_data["solar"]     = solar #
    status_data["battery"]   = battery #battery %
    status_data["vdd"]       = vdd 
    status_data["errcode"]   = status_data_i_got[13] << 8  | status_data_i_got[12]  
    return(status_data)

    
def do_command(command, param):

    # init
    flag = True
    data = {}
    
    # main
    if command=="RESYNC":
        sync_time()
        ok_data = {"Status":"Ok"}
        sending_data = json.dumps(ok_data)

    if command=="START":
        flag = False
    elif command == "STOP":
        flag = False
    elif command=="RESET":
        flag = False
    
    # 'upload' doesn't reach here
    #elif command=="UPLOAD":
        '''
        sending_data = json.dumps(data)
        '''

    elif command=="CAPTURE":
        # CAPTURE 명령어를 받으면, 센서 데이터를 포함한 json file을 client에 넘깁니다.
        data = data_receiving()
        sending_data = json.dumps(data) 
        '''
        f = open('capture.txt', 'r')
        for header in capture_HEADER:
            tmp = f.readline().rstrip()
            if tmp.isdigit():
                data[header] = int(tmp)
            else:
                data[header] = tmp

        tmp_string = ""
        for xyz in range(3):
            tmp_string += f.readline().rstrip()
        data["ac"] = tmp_string
        tmp_string = ""
        for xyz in range(3):
            tmp_string += f.readline().rstrip()
        data["ds"] = tmp_string
                
        sending_data = json.dumps(data)
        '''

    elif command=="STATUS":
        d=get_status_data()
        d["Status"]="Ok"
        sending_data = json.dumps(d)

    elif command=="CONFIG":
        sending_config_data = [0x09]
        Config_data = set_config_data(param)
        #print(Config_data)

        # assuming all values are two bytes
        for tmp in Config_data.values():
            # convert order to GBC parsing
            #sending_config_data.append(tmp >> 8)
            #sending_config_data.append(tmp & 0xFF)
            sending_config_data.append(tmp & 0xff) 
            sending_config_data.append(tmp >> 8)
        rcv = spi.xfer2(sending_config_data)
        Config_data["Status"]="Ok"
        sending_data = json.dumps(Config_data)
        print('CONFIG returns ', sending_data)
    else:
        print('WRONG COMMAND: ', command)
        fail_data = {"Status":"False","Reason":"Wrong Command"}
        sending_data = json.dumps(fail_data)
    
    if flag:
        #sending_data += '\n\n'
	    client_socket.sendall(sending_data.encode()) # encode UTF-8
        #print("Server -> Client :  ", sending_data)
    
#
# Handing socket and commands
#

HOST = ''     # allow all
PORT = 50000  # Use PORT 50000

# Server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
print("Socket ready to listen")

client_socket, addr = server_socket.accept()
#client_socket.setblocking(False)

print('Connected by', addr)
# 소켓 클라이언트와 연결


time_old=datetime.now()
sync_time()
while(1) :
    # read Command
    if select.select([client_socket], [], [], 0.01)[0]: #ready? return in 0.01 sec
        data = client_socket.recv(1024).decode().strip()
        m=re.match("(\w+)(.*)", data)
        #print(m.groups())
        if m:
            cmd=m.groups()[0]
            param=m.groups()[1]
        else:
            print('wrong ',data)
            continue

        now=datetime.now()
        if cmd.startswith("CAPTURE"):
            console_msg=f'\n{cmd} {now.strftime("%H:%M:%S")} +{(now-time_old).total_seconds():.1f} sec'
            time_old=now
        else:
            console_msg=f'\n{cmd} {now.strftime("%H:%M:%S")}'
        do_command(cmd, param)
        print(console_msg)
