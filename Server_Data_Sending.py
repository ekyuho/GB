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
import datetime

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
    
def do_command(command):

    # init
    flag = True
    data = {}
    
    # main
    if command == "START":
        flag = False
    elif command == "STOP":
        flag = False
    elif command == "RESET":
        flag = False
    
    # 'upload' doesn't reach here
    #elif command == "UPLOAD":
        '''
        sending_data = json.dumps(data)
        '''

    elif command == "CAPTURE":
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

    elif command == "STATUS":
        '''
        f = open('status.txt', 'r')
        for header in STATUS:
            tmp = f.readline().rstrip()
            if tmp.isdigit():
                data[header] = int(tmp)
            elif "battery" in header:
                data[header] = float(tmp)
            else:
                data[header] = tmp
        '''
        fail_data = {"Status":"False","Reason":"Not Implemented"}
        sending_data = json.dumps(fail_data)


    elif command == "CONFIG":
        '''
        tmp1 = {}
        tmp2 = {}
        
        Configuration_data = client_socket.recv(1024)
        Configuration_data = Configuration_data.decode()
        Configuration_data = Configuration_data.rstrip() # delete '\n'
        
        config_data = json.loads(Configuration_data)
        
        Format = '%-20s%-20s%-20s\n'
        _print = Format % ('key', 'data', 'data type')
        
        print("ctrigger")
        for key in ctrigger_CONFIG:
            _print += Format %(key, config_data["ctrigger"][key], type(config_data["ctrigger"][key]))
        print(_print)
        
        _print = Format % ('key', 'data', 'data type')
        print("cmeasure")
        for key in cmeasure_CONFIG:
            _print += Format %(key, config_data["cmeasure"][key], type(config_data["cmeasure"][key]))    
        #print(_print)
        '''
        fail_data = {"Status":"False","Reason":"Not Implemented"}
        sending_data = json.dumps(fail_data)
        
    else:
        print('WRONG COMMAND: ', command)
        sending_data = "502 Command Not implemented"
    
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
client_socket.setblocking(False)

print('Connected by', addr)
# 소켓 클라이언트와 연결


time_old=datetime.datetime.now()
while(1) :
    # read Command
    if select.select([client_socket], [], [], 0.01)[0]: #ready? return in 0.01 sec
        cmd = client_socket.recv(1024).decode().strip()
        now=datetime.datetime.now()
        if cmd == "CAPTURE":
            console_msg=f'\n{cmd} {now.strftime("%H:%M:%S")} +{(now-time_old).total_seconds():.1f} sec'
            time_old=now
        else:
            console_msg=f'\n{cmd} {now.strftime("%H:%M:%S")}'
        do_command(cmd)
        print(console_msg)

    
client_socket.close()
server_socket.close()
