import os
import json

root='/home/pi/GB'

# 아래 설정값은 최소 1회만 읽어가고 외부명려어로 값 설정이 있을 경우, 그 뒤부터는 'config.dat' 에 저장시켜두고 그것을 사용한다.
# ctrl command 로 reset 을 실행하거나, config.dat 를 삭제하면 다시 아래값을 1회 읽어간다.

#보드에 장착된 센서에 따라 아래 정의 지정
#새보드 deploy 시 board와  bridge정의가 기본, 추가로 install 에 위치등 값 지정
board=['AC1']
#board=['AC1']
#board=['AC1']
#board=['TI']
#board=['DI','TP']

bridge='1100001'  #교량코드

host="218.232.234.232"  #건교부 테스트 사이트
#host="m.damoa.io"
port=1883

config_ctrigger={}
config_ctrigger["AC1"]={"use":"N","mode":1,"st1high":200,"st1low":"","st2high":"","st2low":"","st3high":"","st4low":"","lt4high":"","st5low":"","st5high":"","st5low":"","bfsec":30,"afsec":60}
config_ctrigger["AC2"]={"use":"N","mode":1,"st1high":200,"st1low":"","st2high":"","st2low":"","st3high":"","st4low":"","lt4high":"","st5low":"","st5high":"","st5low":"","bfsec":30,"afsec":60}
config_ctrigger["AC3"]={"use":"N","mode":1,"st1high":200,"st1low":"","st2high":"","st2low":"","st3high":"","st4low":"","lt4high":"","st5low":"","st5high":"","st5low":"","bfsec":30,"afsec":60}
config_ctrigger["DI"]={"use":"N","mode":3,"st1high":60,"st1low":10,"st2high":"","st2low":"","st3high":"","st4low":"","lt4high":"","st5low":"","st5high":"","st5low":"","bfsec":"","afsec":""}
config_ctrigger["TP"]={"use":"N","mode":3,"st1high":60,"st1low":-20,"st2high":"","st2low":"","st3high":"","st4low":"","lt4high":"","st5low":"","st5high":"","st5low":"","bfsec":"","afsec":""}
config_ctrigger["TI"]={"use":"N","mode":1,"st1high":5,"st1low":-20,"st2high":"","st2low":"","st3high":"","st4low":"","lt4high":"","st5low":"","st5high":"","st5low":"","bfsec":"","afsec":""}

config_time={'zone':'GMT+9','mode':3,'ip':'time.nist.gov','port':80,'period':600} #600sec

c1={'offset':0,'measureperiod':20,'stateperiod':60,'rawperiod':60}
c2={'st1min':1.01, 'st1max':2.01, 'st2min':3.01, 'st2max':4.01, 'st3min':5.01, 'st3max':6.01, 'st4min':7.01, 'st4max':8.01,
    'st5min':9.01, 'st5max':10.01, 'st6min':11.01, 'st6max':12.01, 'st7min':13.01, 'st7max':14.01, 'st8min':15.01, 'st8max':16.01,
    'st9min':17.01, 'st9max':18.01, 'st10min':19.01, 'st10max':20.01}
config_cmeasure={}
config_cmeasure['AC1']={'sensitivity':20,'samplerate':100,'usefft':'N'}
config_cmeasure['AC2']={'sensitivity':20,'samplerate':100,'usefft':'N'}
config_cmeasure['AC3']={'sensitivity':20,'samplerate':100,'usefft':'N'}
config_cmeasure['DI']={'sensitivity':24,'samplerate':1/600,'usefft':'N'}
config_cmeasure['TP']={'sensitivity':16,'samplerate':1/600,'usefft':'N'}
config_cmeasure['TI']={'sensitivity':20,'samplerate':1/600,'usefft':'N'}
config_cmeasure['AC1'].update(c1)
config_cmeasure['AC1'].update(c2)
config_cmeasure['AC2'].update(c1)
config_cmeasure['AC2'].update(c2)
config_cmeasure['AC3'].update(c1)
config_cmeasure['AC3'].update(c2)
config_cmeasure['DI'].update(c1)
config_cmeasure['TP'].update(c1)
config_cmeasure['TI'].update(c1)

config_connect={'cseip':'218.232.234.234','cseport':7579,'csename':'cse-gnrb-mon','cseid':'cse-gnrb-mon','mqttip':'218.232.234.234','mqttport':1883,'uploadip':'218.232.234.234','uploadport':80}

info_manufacture={}
info_manufacture['AC1']={'serial':'','manufacturer':'Ino-on. Inc.','phonenumber':'02-336-2050','website':'http://www.ino-on.com','model':'mgi-1000','sensortype':'MEMS','sensitivity':'20bit','opertemp':'-20~60℃','manufacturedate':'2022-04-19','fwver':'v1.0','hwver':'v1.0','hwtype':'D','mac':''}
info_manufacture['AC2']={'serial':'','manufacturer':'Ino-on. Inc.','phonenumber':'02-336-2051','website':'http://www.ino-on.com','model':'mgi-1000','sensortype':'MEMS','sensitivity':'20bit','opertemp':'-20~60℃','manufacturedate':'2022-04-19','fwver':'v1.0','hwver':'v1.0','hwtype':'D','mac':''}
info_manufacture['AC3']={'serial':'','manufacturer':'Ino-on. Inc.','phonenumber':'02-336-2052','website':'http://www.ino-on.com','model':'mgi-1000','sensortype':'MEMS','sensitivity':'20bit','opertemp':'-20~60℃','manufacturedate':'2022-04-19','fwver':'v1.0','hwver':'v1.0','hwtype':'D','mac':''}
info_manufacture['DI']={'serial':'','manufacturer':'Ino-on. Inc.','phonenumber':'02-336-2053','website':'http://www.ino-on.com','model':'mgi-1000','sensortype':'Wire-strain','sensitivity':'24bit','opertemp':'-20~60℃','manufacturedate':'2022-04-19','fwver':'v1.0','hwver':'v1.0','hwtype':'D','mac':''}
info_manufacture['TP']={'serial':'','manufacturer':'Ino-on. Inc.','phonenumber':'02-336-2054','website':'http://www.ino-on.com','model':'mgi-1000','sensortype':'CMOS','sensitivity':'12bit','opertemp':'-20~60℃','manufacturedate':'2022-04-19','fwver':'v1.0','hwver':'v1.0','hwtype':'D','mac':''}
info_manufacture['TI']={'serial':'','manufacturer':'Ino-on. Inc.','phonenumber':'02-336-2055','website':'http://www.ino-on.com','model':'mgi-1000','sensortype':'MEMS','sensitivity':'0.01º','opertemp':'-20~60℃','manufacturedate':'2022-04-19','fwver':'v1.0','hwver':'v1.0','hwtype':'D','mac':''}

info_install={}
info_install['AC1']={'date':'2022-04-25','sensorid':'AC_A1_01_X','place':'금남2교(하)','plccecode':'25731','location':'6.7m(P2~P3)','section':'최우측 거더','latitude':'37.657248','longitude':'127.359962','aetype':'S'}
info_install['AC2']={'date':'2022-04-25','sensorid':'AC_A1_02_X','place':'금남2교(하)','plccecode':'25731','location':'6.7m(P2~P3)','section':'최우측 거더','latitude':'37.657248','longitude':'127.359962','aetype':'S'}
info_install['AC3']={'date':'2022-04-25','sensorid':'AC_A1_03_X','place':'금남2교(하)','plccecode':'25731','location':'6.7m(P2~P3)','section':'최우측 거더','latitude':'37.657248','longitude':'127.359962','aetype':'S'}
info_install['DI']={'date':'2022-04-25','sensorid':'DI_A1_01_X','place':'금남2교(하)','plccecode':'25731','location':'6.7m(P2~P3)','section':'최우측 거더','latitude':'37.657248','longitude':'127.359962','aetype':'S'}
info_install['TP']={'date':'2022-04-25','sensorid':'TP_A1_01_X','place':'금남2교(하)','plccecode':'25731','location':'6.7m(P2~P3)','section':'최우측 거더','latitude':'37.657248','longitude':'127.359962','aetype':'S'}
info_install['TI']={'date':'2022-04-25','sensorid':'TI_A1_01_X','place':'금남2교(하)','plccecode':'25731','location':'6.7m(P2~P3)','section':'최우측 거더','latitude':'37.657248','longitude':'127.359962','aetype':'S'}

info_imeasure={}
info_imeasure['AC1']={'mode':'D','type':'AC','item':'가속도','range':'2G','precision':'0.01','accuracy':'0.01','meaunit':'mg','meaunit':'','direction':''}
info_imeasure['AC2']={'mode':'D','type':'AC','item':'가속도','range':'2G','precision':'0.01','accuracy':'0.01','meaunit':'mg','meaunit':'','direction':''}
info_imeasure['AC3']={'mode':'D','type':'AC','item':'가속도','range':'2G','precision':'0.01','accuracy':'0.01','meaunit':'mg','meaunit':'','direction':''}
info_imeasure['DI']={'mode':'S','type':'DI','item':'변위','range':'','precision':'1','accuracy':'3','meaunit':'ustrain','meaunit':'','direction':''}
info_imeasure['TP']={'mode':'S','type':'TP','item':'온도','range':'-40~+120','precision':'0.01','accuracy':'0.01','meaunit':'C','meaunit':'','direction':''}
info_imeasure['TI']={'mode':'S','type':'TI','item':'경사(각도)','range':'0~90','precision':'0.01','accuracy':'0.01','meaunit':'degree','meaunit':'','direction':''}

data_dtrigger={}

state={'battery':0,'memory':0,'disk':0,'cpu':0,'time':'yyyy-MM-dd HH:mm:ss.ffff','uptime':'0 days, 13:29:34','abflag':'N','abtime':'','abdesc':'','solarinputvolt':0,'solarinputamp':0,'solarchargevolt':0,'powersupply':0}

ctrl={'cmd':''}
# 'reset','reboot  synctime','fwupdate','realstart','realstop','reqstate','settrigger','settime','setmeasure','setconnect','measurestart','meaurestop'


cse={'name':'cse-gnrb-mon'}
ae={}
if 'AC1' in board:
    ae[F'ae.{bridge}-AC_A1_01_X']={
        'config':{'ctrigger':config_ctrigger['AC1'], 'time':config_time, 'cmeasure':config_cmeasure['AC1'], 'connect':config_connect},
        'info':{'manufacture':info_manufacture['AC1'], 'install':info_install['AC1'],'imeasure':info_imeasure['AC1']},
        'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
        'state':state,
        'ctrl':{"sub":1}
    }

if 'AC2' in board:
	ae[F'ae.{bridge}-AC_A1_02_X']={
	    'config':{'ctrigger':config_ctrigger['AC2'], 'time':config_time, 'cmeasure':config_cmeasure['AC2'], 'connect':config_connect},
	    'info':{'manufacture':info_manufacture['AC2'], 'install':info_install['AC2'],'imeasure':info_imeasure['AC2']},
	    'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
	    'state':state,
	    'ctrl':{"sub":1}
	}
	
if 'AC3' in board:
	ae[F'ae.{bridge}-AC_A1_03_X']={
	    'config':{'ctrigger':config_ctrigger['AC3'], 'time':config_time, 'cmeasure':config_cmeasure['AC3'], 'connect':config_connect},
	    'info':{'manufacture':info_manufacture['AC3'], 'install':info_install['AC3'],'imeasure':info_imeasure['AC3']},
	    'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
	    'state':state,
	    'ctrl':{"sub":1}
	}
	
if 'DI' in board:
	ae[F'ae.{bridge}-DI_A1_01_X']={
	    'config':{'ctrigger':config_ctrigger['DI'], 'time':config_time, 'cmeasure':config_cmeasure['DI'], 'connect':config_connect},
	    'info':{'manufacture':info_manufacture['DI'], 'install':info_install['DI'],'imeasure':info_imeasure['DI']},
	    'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
	    'state':state,
	    'ctrl':{"sub":1}
	}
	
if 'TP' in board:
	ae[F'ae.{bridge}-TP_A1_01_X']={
	    'config':{'ctrigger':config_ctrigger['TP'], 'time':config_time, 'cmeasure':config_cmeasure['TP'], 'connect':config_connect},
	    'info':{'manufacture':info_manufacture['TP'], 'install':info_install['TP'],'imeasure':info_imeasure['TP']},
	    'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
	    'state':state,
	    'ctrl':{"sub":1}
	}
	
if 'TI' in board:
	ae[F'ae.{bridge}-TI_A1_01_X']={
	    'config':{'ctrigger':config_ctrigger['TI'], 'time':config_time, 'cmeasure':config_cmeasure['TI'], 'connect':config_connect},
	    'info':{'manufacture':info_manufacture['TI'], 'install':info_install['TI'],'imeasure':info_imeasure['TI']},
	    'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
	    'state':state,
	    'ctrl':{"sub":1}
	}



# mqtt를 사용할 것인지, 그렇다면 어느 센서의 데이터를 보낼지에 대한 딕셔너리
mqtt_list = {
    "use":"Y",
    "acc1":"Y",
    "acc2":"N",
    "acc3":"N",
    "dis":"N",
    "tem":"N",
    "deg":"N"
    }

# mqtt 데이터에 보낼 samplerate list. 정적 데이터의 경우 1초에 1개를 보내기 때문에 1, 동적 데이터의 경우 1초에 들어오는 데이터 개수만큼의 samplerate를 설정해두었다
# 참고 : 원래 samplerate는 oneM2M서버의 config->cmeasure에 존재. 서버에 입력되어있는 samplerate는 자료형이 string이기 때문에 int로 변환 필요.
samplerate_list = {
    "acc1":100,
    "acc2":100,
    "acc3":100,
    "dis":1,
    "tem":1,
    "deg":1
    }

TOPIC_list = {
    "acc1":F'/{cse["name"]}/ae.{bridge}-AC_A1_01_X/realtime',
    "acc2":F'/{cse["name"]}/ae.{bridge}-AC_A1_02_X/realtime',
    "acc3":F'/{cse["name"]}/ae.{bridge}-AC_A1_03_X/realtime',
    "dis":F'/{cse["name"]}/ae.{bridge}-DI_A1_01_X/realtime',
    "tem":F'/{cse["name"]}/ae.{bridge}-TP_A1_01_X/realtime',
    "deg":F'/{cse["name"]}/ae.{bridge}-TI_A1_01_X/realtime'
    }

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
