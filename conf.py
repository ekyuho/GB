import os
import json

root='/home/pi/GB'

# 아래 설정값은 최소 1회만 읽어가고 외부명령어로 값 설정이 있을 경우, 그 뒤부터는 'config.dat' 에 저장시켜두고 그것을 사용한다.
# ctrl command 로 reset 을 실행하거나, config.dat 를 삭제하면 다시 아래값을 1회 읽어간다.

#####################################################################

supported_sensors = {'AC', 'DI', 'TP', 'TI'}

#####################################################################
#### 다음 섹션은 센서별 generic factory 초기설정값
#####################################################################
config_ctrigger={}
config_ctrigger["AC"]={"use":"Y","mode":1,"st1high":200,"st1low":-2000,"bfsec":30,"afsec":60}
config_ctrigger["DI"]={"use":"Y","mode":3,"st1high":60,"st1low":10,"bfsec":0,"afsec":1}
config_ctrigger["TP"]={"use":"Y","mode":3,"st1high":60,"st1low":-20,"bfsec":0,"afsec":1}
config_ctrigger["TI"]={"use":"Y","mode":3,"st1high":5,"st1low":-20,"bfsec":0,"afsec":1}
# saved for copy just in case
#{"use":"Y","mode":1,"st1high":200,"st1low":-2000,"st2high":"","st2low":"","st3high":"","st4low":"","lt4high":"","st5low":"","st5high":"","st5low":"","bfsec":30,"afsec":60}

config_cmeasure={}
config_cmeasure['AC']={'sensitivity':20,'samplerate':"100",'usefft':'Y'}
config_cmeasure['DI']={'sensitivity':24,'samplerate':"1",'usefft':'N'}
config_cmeasure['TP']={'sensitivity':16,'samplerate':"1",'usefft':'N'}
config_cmeasure['TI']={'sensitivity':20,'samplerate':"1",'usefft':'N'}

cmeasure2={'offset':0,'measureperiod':600,'stateperiod':60,'rawperiod':60,
    'st1min':2.1, 'st1max':2.6, 'st2min':3.01, 'st2max':4.01, 'st3min':5.01, 'st3max':6.01, 'st4min':7.01, 'st4max':8.01,
        'st5min':9.01, 'st5max':10.01, 'st6min':11.01, 'st6max':12.01, 'st7min':13.01, 'st7max':14.01, 'st8min':15.01, 'st8max':16.01,
        'st9min':17.01, 'st9max':18.01, 'st10min':19.01, 'st10max':20.01}
config_cmeasure['AC'].update(cmeasure2)  #deep copy
config_cmeasure['DI'].update(cmeasure2)  #deep copy
config_cmeasure['TP'].update(cmeasure2)  #deep copy
config_cmeasure['TI'].update(cmeasure2)  #deep copy


info_manufacture={}
info_manufacture['AC']={'serial':'','manufacturer':'Ino-on. Inc.','phonenumber':'02-336-2050','website':'http://www.ino-on.com','model':'mgi-1000',
    'sensortype':'MEMS','sensitivity':'20bit','opertemp':'-20~60℃','manufacturedate':'2022-04-19','fwver':'1.0','hwver':'1.0','hwtype':'D','mac':''}
info_manufacture['DI']={'serial':'','manufacturer':'Ino-on. Inc.','phonenumber':'02-336-2053','website':'http://www.ino-on.com','model':'mgi-1000',
    'sensortype':'Wire-strain','sensitivity':'24bit','opertemp':'-20~60℃','manufacturedate':'2022-04-19','fwver':'1.0','hwver':'1.0','hwtype':'D','mac':''}
info_manufacture['TP']={'serial':'','manufacturer':'Ino-on. Inc.','phonenumber':'02-336-2054','website':'http://www.ino-on.com','model':'mgi-1000',
    'sensortype':'CMOS','sensitivity':'12bit','opertemp':'-20~60℃','manufacturedate':'2022-04-19','fwver':'1.0','hwver':'1.0','hwtype':'D','mac':''}
info_manufacture['TI']={'serial':'','manufacturer':'Ino-on. Inc.','phonenumber':'02-336-2055','website':'http://www.ino-on.com','model':'mgi-1000',
    'sensortype':'MEMS','sensitivity':'0.01º','opertemp':'-20~60℃','manufacturedate':'2022-04-19','fwver':'1.0','hwver':'1.0','hwtype':'D','mac':''}


info_imeasure={}
info_imeasure['AC']={'mode':'D','type':'AC','item':'가속도','range':'2G','precision':'0.01','accuracy':'0.01','meaunit':'mg','meaunit':'','direction':''}
info_imeasure['DI']={'mode':'S','type':'DI','item':'변위','range':'','precision':'1','accuracy':'3','meaunit':'ustrain','meaunit':'','direction':''}
info_imeasure['TP']={'mode':'S','type':'TP','item':'온도','range':'-40~+120','precision':'0.01','accuracy':'0.01','meaunit':'C','meaunit':'','direction':''}
info_imeasure['TI']={'mode':'S','type':'TI','item':'경사(각도)','range':'0~90','precision':'0.01','accuracy':'0.01','meaunit':'degree','meaunit':'','direction':''}

data_dtrigger={"time":"","step":"","mode":"","sthigh":"","stlow":"","val":"","start":"","samplerate":"","count":"","data":""}
data_fft={"start":"","end":"","st1hz":"","st2hz":"","st3hz":"","st4hz":"","st5hz":"","st6hz":"","st7hz":"","st8hz":"","st9hz":"","st10hz":""}
data_dmeasure={"type":"","time":"","temp":"","hum":"","val":"","min":"","max":"","avg":"","std":"","rms":"","peak":""}

ae={}
TOPIC_list = {}

def make_ae(aename, install):
    global TOPIC_list, ae
    global config_ctrigger, config_time, config_cmeasure, config_connect, info_manufacture, info_imeasure, state, data_dtrigger, data_fft, data_dmeasure
    sensor_id= aename.split('-')[1]
    sensor_type = sensor_id[0:2]
    if not sensor_type in supported_sensors:
        print('unknown sensor definition')
        return

    ae[aename]= {
        'config':{'ctrigger':{}, 'time':{}, 'cmeasure':{}, 'connect':{}},
        'info':{'manufacture':{}, 'install':{},'imeasure':{}},
        'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
        'state':state,
        'ctrl':{"cmd":"","targetid":""}
    }
    ae[aename]['config']['ctrigger'].update(config_ctrigger[sensor_type])
    ae[aename]['config']['time'].update(config_time)
    ae[aename]['config']['cmeasure'].update(config_cmeasure[sensor_type])
    ae[aename]['config']['connect'].update(config_connect)
    ae[aename]['info']['manufacture'].update(info_manufacture[sensor_type])
    ae[aename]['info']['install'].update(install)
    ae[aename]['info']['install']['sensorid']=sensor_id
    ae[aename]['info']['imeasure'].update(info_imeasure[sensor_type])
    ae[aename]['state'].update(state)
    ae[aename]['data']['dtrigger'].update(data_dtrigger)
    ae[aename]['data']['fft'].update(data_fft)
    ae[aename]['data']['dmeasure'].update(data_dmeasure)
    TOPIC_list[aename]=F'/{cse["name"]}/{aename}/realtime'
    ae[aename]['local']={}
    if sensor_type in {'AC', 'DI', 'TI', 'TP'}:   # 얘만 mqtt default 로  가동
        ae[aename]['local']['realstart']='Y'
        ae[aename]['local']['measurestart'] ='Y' 
    else:
        ae[aename]['local']['realstart']='N'
        ae[aename]['local']['measurestart']='N'
    

#####################################################################
####   다음 섹션은 설치관련한 설정값
#####################################################################

host="218.232.234.232"  #건교부 테스트 사이트
port=1883
cse={'name':'cse-gnrb-mon'}

config_time={'zone':'GMT+9','mode':3,'ip':'time.nist.gov','port':80,'period':600} #600sec
config_connect={'cseip':'218.232.234.232','cseport':7579,'csename':'cse-gnrb-mon','cseid':'cse-gnrb-mon','mqttip':'218.232.234.232','mqttport':1883,'uploadip':'218.232.234.232','uploadport':80}
state={'battery':0,'memory':0,'disk':0,'cpu':0,'time':'yyyy-MM-dd HH:mm:ss.ffff','uptime':'0 days, 13:29:34','abflag':'N','abtime':'','abdesc':'','solarinputvolt':0,'solarinputamp':0,'solarchargevolt':0,'powersupply':0}

ctrl={'cmd':''}
# 'reset','reboot  synctime','fwupdate','realstart','realstop','reqstate','settrigger','settime','setmeasure','setconnect','measurestart','meaurestop'


#####################################################################
####   다음 섹션은 해당노드의 센서 정보 구성
#####################################################################

install= {'date':'2022-04-25','place':'금남2교(하)','plccecode':'25731','location':'6.7m(P2~P3)','section':'최우측 거더','latitude':'37.657248','longitude':'127.359962','aetype':'S'}

make_ae('ae.12345141-AC_SIM_01_X', install)
make_ae('ae.12345141-DI_SIM_01_X', install)
make_ae('ae.12345141-TP_SIM_01_X', install)
make_ae('ae.12345141-TI_SIM_01_X', install)


FFT_data_acc = {
    "use":"Y",
    "st1min":2.1,
    "st1max":2.6
    }

FFT_data_str = {
    "use":"N",
    "st1min":2.1,
    "st1max":2.6
    }
    
if os.path.exists(F"{root}/config.dat"): 
    print('read from config.dat')
    with open(F"{root}/config.dat") as f:
        try:
            ae = json.load(f)
        except ValueError as e:
            print(e)
            print('wrong config.dat')
else:
    print('read from conf.py')

print(f'read {list(ae.keys())}')

if __name__ == "__main__":
    print(ae)
