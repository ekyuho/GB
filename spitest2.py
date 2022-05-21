#spi test v2.1
#date : 2022-04-27
#writer : ino-on joosa
#variable value printing available

import spidev
import time
import numpy as np
import math

spi_bus = 0
spi_device = 0
spi = spidev.SpiDev()
spi.open(spi_bus, spi_device)
spi.max_speed_hz = 100000 #100MHz

rq_cmd = [0x01]*6
CMD_A = [0x10]*6
CMD_B = [0x20]*6


def request_cmd() :
    RXD = spi.xfer2(rq_cmd)
    print(RXD)
    if   RXD == [0x2, 0x3, 0x4, x6, 0x7] : # ACK
        return 1
    else : 
        return 0

def send_data(cmd) : 
    RXD = spi.xfer3(cmd)
    print(RXD)
    return RXD

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
def basic_conversion(number_list):
    result_str = ''
    for i in reversed(range(len(number_list))):
        result_hex = hex(number_list[i])[2:]
        if len(result_hex)<2:
            result_hex = '0'+result_hex
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
    result = (result-5524097)/173
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
    #result_str = result_str[::-1] # invert string
    #print("raw hex data :", result_str)
    result_int = Twos_Complement(result_str, 4)
    result = float(result_int)
    result *= 0.0039
    result = round(result, 2)
    #print("conversion result :", result)
    return result

def deg_conversion(number_list):
    result_str = ''
    for i in reversed(range(len(number_list))):
        result_hex = hex(number_list[i])[2:]
        if len(result_hex)<2:
            result_hex = '0'+result_hex
        result_str += result_hex
    #result_str = result_str[::-1] # invert string
    #print("hex value :", result_str)
    #result_int = int(result_str, 16)
    #result_int = -(result_int & 0x80000000) | (result_int & 0x7fffffff)
    result_int = Twos_Complement(result_str, 2)
    result = float(result_int)
    result /= 100
    return result

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
    

i =0
d = 1
ds = 0.01
d2 = 0.1
n = 2400

isReady = False

while(1) : 

    #print("s 111111");
    #print(spi.xfer2([1]) )
    
    print("s:"+ "0x24", end=' ')		# request header
    rcv1 = spi.xfer2([0x24])
    #print(rcv1)
    #print("header data signal")
    time.sleep(ds)

    print("s:"+ "0x40", end=' ')
    rcv2 = spi.xfer2([0x40]*8) # follow up action
    #print(rcv2)
    
    if rcv2[0] == 216 and rcv2[1] == 216:
        isReady = True
        json_data = {}
        print("data is ready")
        status = basic_conversion(rcv2[2:4]) #status info save
        timestamp = basic_conversion(rcv2[4:8]) #timestamp info save
        #print("status =", status, "timestamp = ", timestamp)
        json_data["Timestamp"] = timestamp
        json_data["Status"] = status
        time.sleep(ds)
    else:
        isReady = False
        print("-> error")
        
    if isReady: #only send data if data is ready
        print("s:"+ "0x26")		# request static
        rcv3 = spi.xfer2([0x26])
        #print(rcv3)
        print("static sensor data signal")
        time.sleep(ds)

        print("s:"+ "0x40")
        rcv4 = spi.xfer2([0x40]*16) # follow up action
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
 
        print("s:"+ "0x25")        # request data	
        rcv5 = spi.xfer2([0x25])
        #print(rcv5)
        print("Dynamic sensor data signal")
        time.sleep(ds)

        print("s:"+ "0x40")
        rcv6 = spi.xfer2([0x40]*n)
        #print(rcv6)
        '''
        for i in range(len(rcv6)//4):
            print("Value No.", i+1, ": ",hex(rcv6[i]), hex(rcv6[i+1]), hex(rcv6[i+2]), hex(rcv6[i+3]))
        '''
        acc_list = list()
        strain_list = list()
        for i in range(100):
            cycle = i*24
            ax = acc_conversion(rcv6[0+cycle:4+cycle])
            ay = acc_conversion(rcv6[4+cycle:8+cycle])
            az = acc_conversion(rcv6[8+cycle:12+cycle])
            acc_list.append({"x":ax, "y":ay, "z":az})
            sx = basic_conversion(rcv6[12+cycle:16+cycle])
            sy = basic_conversion(rcv6[16+cycle:20+cycle])
            sz = basic_conversion(rcv6[20+cycle:24+cycle])
            strain_list.append({"x":sx, "y":sy, "z":sz})
        '''
        print("Acceleration list print")
        for i in range(len(acc_list)):
            print("Accelration No.", i+1, ":", acc_list[i][0], acc_list[i][1], acc_list[i][2])
        for i in range(len(strain_list)):
            print("Strain No.", i+1, ":", strain_list[i][0], strain_list[i][1], strain_list[i][2])
        '''
        json_data["Acceleration"] = acc_list
        json_data["Strain"] = strain_list
        
        # wish_data : data which want to see
        # list of data : Degree, Temperature, Displacement, Acceleration, Strain
        #wish_data = "Displacement"
        wish_data = "Acceleration"
        
        print(wish_data,"printing")
        print(json_data[wish_data])
        
        time.sleep(d2)

        print(" ")
           

    time.sleep(0.5)
