# Server_Data_Sending.py
# date : 2022-05-06
# 초기 작성자 : ino-on, 주수아
# 소켓 클라이언트와 통신을 하며, 클라이언트가 명령어를 보낼 때마다 명령어에 따른 동작을 수행합니다.
# 현재 'CAPTURE' 명령어만이 활성화되어있습니다. 

#   5/6 변위식 수정. 추후 인하대쪽 코드와 통합할 예정입니다, 주수아
#   5/5 making robust를 위한 작업들, 김규호 

VERSION="V1.1"

import spidev
import time
import numpy as np
import socket
import select
import json
import math
from datetime import datetime
from datetime import timedelta
import re
import os
import create
import conf
cse = conf.cse
ae = conf.ae


spi_bus = 0
spi_device = 0
spi = spidev.SpiDev()
spi.open(spi_bus, spi_device)
spi.max_speed_hz = 100000 #100MHz

console_msg=""
#하드웨어 보드의 설정상태 저장
board_setting = {} 

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

def status_conversion(solar, battery, vdd):
    solar   = 0.003013 * solar + 1.2824
    battery = battery / 4096 * 100  # 12-bit
    vdd     = vdd / 4096 * 100      # 12-bit

    return solar, battery, vdd

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
    
    
# str basic_conversion(list number_list)
# convert whole bit data to demical
# 특별한 연산 없이 bit data를 원래 순서대로 뒤집어둡니다. 
def basic_conversion(number_list):
    result_str = ''
    for i in reversed(range(len(number_list))):
        result_hex = hex(number_list[i])[2:]
        if len(result_hex)<2:
            result_hex = '0'+result_hex
        result_str += result_hex
    return result_str

# dict status_trigger_return(hex_data)
# status bit를 분석하여 trigger가 발동된 센서가 있는지 표기합니다.
# trigger가 발동되었다면 "1"을, 그렇지 않았다면 "0"을 저장하고 있습니다.
def status_trigger_return(hex_data):
    #print("hex data :", hex_data)
    int_data = int(hex_data, 16)
    #print("int_data :", int_data)
    raw_bin_data = bin(int_data)
    raw_bin_data = "0b"+"00000"+raw_bin_data[2:]
    #print("raw_bin_data :", raw_bin_data)
    bin_data = raw_bin_data[len(raw_bin_data)-8:len(raw_bin_data)-3] #trigger 여부를 나타내는 data 5칸을 표기
    #print("bin_data :", bin_data)
    tem_bit = bin_data[0]
    dis_bit = bin_data[1]
    str_bit = bin_data[2]
    deg_bit = bin_data[3]
    acc_bit = bin_data[4]

    is_triggered = {
        "Temperature":tem_bit,
        "Displacement":dis_bit,
        "Strain":str_bit,
        "Degree":deg_bit,
        "Acceleration":acc_bit
    }

    return is_triggered

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

TimeCorrection = int(ds * 1000) # FIXME

isReady = False

upload_HEADER = ["Timestamp", "Temperature", "Displacement"]
capture_HEADER = ["Timestamp", "Temperature", "Displacement", "samplerate"]
ctrigger_CONFIG = ["use", "mode", "st1high", "st1low", "bfsec"]
cmeasure_CONFIG = ["sensitivity", "samplerate", "measureperiod", "stateperiod", "rawperiod"]
STATUS = ["ibattery", "ebattery", "count", "abflag", "abtime", "abdesc"]
num_of_DATA = 2

Config_datas = {}        # config data 담을 dict
Status_datas = {}        # status data 담을 dict
BaseTimeStamp = 0
BaseTime = datetime.now()   # basetime , 처음 동작할 때 다시 초기화함
TimeCorrection = int(ds * 1000) # FIXME

# AE별 global offset value, defaulted to 0
Offset={'ac':0,'di':0,'ti':0,'tp':0}

# dict data_receiving()
# 센서로부터 data bit를 받아, 그것을 적절한 int값으로 변환합니다.
# return value는 모든 센서 데이터를 포함하고 있는 dictionary 데이터입니다.
def data_receiving():
    global console_msg
    global Offset
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
        #print("trigger status : ", status_trigger_return(status)) #trigger 작동여부 출력 테스트 코드
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
        """
        degreeX = deg_conversion(rcv4[0:2])
        degreeY = deg_conversion(rcv4[2:4])
        degreeZ = deg_conversion(rcv4[4:6])
        Temperature = tem_conversion(rcv4[6:8])
        Displacement_ch4 = dis_conversion(rcv4[8:12])
        Displacement_ch5 = basic_conversion(rcv4[12:])
        """
        degreeX = deg_conversion(rcv4[0:2]) + Offset['ti'] 
        degreeY = deg_conversion(rcv4[2:4]) + Offset['ti'] 
        degreeZ = deg_conversion(rcv4[4:6]) + Offset['ti'] 
        Temperature = tem_conversion(rcv4[6:8]) + Offset['tp'] 
        Displacement_ch4 = dis_conversion(rcv4[8:12]) + Offset['di']
        # 식을 dis_conversion으로 변경하여 해결하였음
        Displacement_ch5 = dis_conversion(rcv4[12:]) + Offset['di']
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
            ax = acc_conversion(rcv6[0+cycle:4+cycle]) + Offset['ac'] 
            ay = acc_conversion(rcv6[4+cycle:8+cycle]) + Offset['ac'] 
            az = acc_conversion(rcv6[8+cycle:12+cycle]) + Offset['ac'] 
            acc_list.append({"x":ax, "y":ay, "z":az})
            #acc_list.append([ax, ay, az])
            """
            ax = acc_conversion(rcv6[0+cycle:4+cycle])
            ay = acc_conversion(rcv6[4+cycle:8+cycle])
            az = acc_conversion(rcv6[8+cycle:12+cycle])
            """
            sx = basic_conversion(rcv6[12+cycle:16+cycle])
            sy = basic_conversion(rcv6[16+cycle:20+cycle])
            sz = basic_conversion(rcv6[20+cycle:24+cycle])
            strain_list.append({"x":sx, "y":sy, "z":sz})
            #strain_list.append([sx, sy, sz])           

        json_data["Acceleration"] = acc_list
        json_data["Strain"] = strain_list
        time.sleep(d2)
        j=json.dumps(json_data, ensure_ascii=False)
        console_msg += F" {len(j)}B {j[0:60]} ..."
        return json_data

def set_config_data(config_data):
    jdata = json.loads(config_data)
    aename=jdata["aename"]
    config=jdata["config"]

    print(f'set_config({aename} {config["ctrigger"]} {config["cmeasure"]}')

    global Offset
    # set offset, already defauled to 0
    if '-AC_' in aename: Offset['ac'] = config['cmeasure']['offset']  
    if '-DI_' in aename: Offset['di'] = config['cmeasure']['offset']  
    if '-TI_' in aename: Offset['ti'] = config['cmeasure']['offset']  
    if '-TP_' in aename: Offset['tp'] = config['cmeasure']['offset']  
    
    # making triger_seltect
    ttp = tdi = tti = tac = 0
    tp1h = tp1l = di1h = di1l = ti1h = ti1l = ac1h = 0

    if '-AC_' in aename and 'use' in config['ctrigger'] and config['ctrigger']['use'] in {'Y','y'}: 
        tac = int(0x0100)
        if 'st1high' in config['ctrigger'] and str(config['ctrigger']['st1high']).isnumeric(): ac1h = int(config['ctrigger']['st1high'])
    if '-DI_' in aename and 'use' in config['ctrigger'] and config['ctrigger']['use'] in {'Y','y'}:
        tdi = int(0x0800)
        if 'st1high' in config['ctrigger'] and str(config['ctrigger']['st1high']).isnumeric(): di1h = int(config['ctrigger']['st1high'])
        if 'st1low' in config['ctrigger'] and str(config['ctrigger']['st1high']).isnumeric(): di1l = int(config['ctrigger']['st1low'])
        di1l = config['ctrigger']['st1low']
    if '-TI_' in aename and 'use' in config['ctrigger'] and config['ctrigger']['use'] in {'Y','y'}:
        tti = int(0x0200)
        if 'st1high' in config['ctrigger'] and str(config['ctrigger']['st1high']).isnumeric(): ti1h = int(config['ctrigger']['st1high'])
        if 'st1low' in config['ctrigger'] and str(config['ctrigger']['st1high']).isnumeric(): ti1l = int(config['ctrigger']['st1low'])
    if '-TP_' in aename and 'use' in config['ctrigger'] and config['ctrigger']['use'] in {'Y','y'}:
        ttp = int(0x1000)
        if 'st1high' in config['ctrigger'] and str(config['ctrigger']['st1high']).isnumeric(): tp1h = int(config['ctrigger']['st1high'])
        if 'st1low' in config['ctrigger'] and str(config['ctrigger']['st1high']).isnumeric(): tp1l = int(config['ctrigger']['st1low'])

    # formatting for GBC data structure and tranmisssion (two bytes) 
    # Revise latter!!!
    global board_setting
    board_setting['samplingRate'] =   int(np.uint16(100))           # hw fix 5/9
    board_setting['sensingDuration'] = int(np.uint16(12*60*60))     # hw fix 5/9
    board_setting['measurePeriod'] =  int(np.uint16(1))             # SC support 5/9 
    board_setting['uploadPeriod'] =   int(np.uint16(6))             # hSC support 5/9
    board_setting['sensorSelect'] =   int(np.uint16(ttp|tdi|tti|tac))
    board_setting['highTemp'] =       int(np.int16(tp1h*100))
    board_setting['lowTemp'] =        int(np.int16(tp1l*100))
    board_setting['highDisp'] =       int(np.int16(di1h*100))
    board_setting['lowDisp'] =        int(np.int16(di1l*100))
    board_setting['highStrain'] =     int(np.int16(0))
    board_setting['lowStrain'] =      int(np.int16(0))
    board_setting['highTilt'] =       int(np.int16(ti1h*100))
    board_setting['lowTilt'] =        int(np.int16(ti1l*100))
    board_setting['highAcc'] =        int(np.uint16(ac1h/0.0039/16))
    board_setting['lowAcc'] =         int(np.int16(0))       # hw fix 5/9
    # end of formatting 
    return board_setting 


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
        sending_data = json.dumps(ok_data, ensure_ascii=False)

    if command=="START":
        flag = False
    elif command == "STOP":
        flag = False
    elif command=="RESET":
        flag = False
    
    # 'upload' doesn't reach here
    #elif command=="UPLOAD":
        '''
        sending_data = json.dumps(data, ensure_ascii=False)
        '''

    elif command=="CAPTURE":
        # CAPTURE 명령어를 받으면, 센서 데이터를 포함한 json file을 client에 넘깁니다.
        data = data_receiving()
        sending_data = json.dumps(data, ensure_ascii=False) 
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
                
        sending_data = json.dumps(data, ensure_ascii=False)
        '''

    elif command=="STATUS":
        d=get_status_data()
        d["Status"]="Ok"
        sending_data = json.dumps(d, ensure_ascii=False)

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
        ok_data = {"Status":"Ok"}
        sending_data = json.dumps(ok_data, ensure_ascii=False)
        print('CONFIG returns ', sending_data)
    else:
        print('WRONG COMMAND: ', command)
        fail_data = {"Status":"False","Reason":"Wrong Command"}
        sending_data = json.dumps(fail_data, ensure_ascii=False)
    
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

root='/home/pi/GB'
if os.path.exists(f'{root}/newfile.txt'):
    os.remove(f'{root}/newfile.txt')
    for aename in ae:
        ae[aename]["info"]["manufacture"]["fwver"]=VERSION
        create.ci(aename, 'info', 'manufacture')


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
            if len(m.groups())>1:
                param=m.groups()[1]
        else:
            continue

        now=datetime.now()
        if cmd.startswith("CAPTURE"):
            console_msg=f'\n{cmd} {now.strftime("%H:%M:%S")} +{(now-time_old).total_seconds():.1f} sec'
            time_old=now
        else:
            console_msg=f'\n{cmd} {now.strftime("%H:%M:%S")}'
        do_command(cmd, param)
        print(console_msg)
