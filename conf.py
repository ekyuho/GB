host="m.damoa.io"
#host="218.232.234.232"  #건교부 테스트 사이트
port=1883
bridge='323376'  #교량코드

config_ctrigger={}
config_ctrigger['AC1']={'use':'Y','mode':1,'st1high':200,'bfsec':0.015,'afsec':120}
config_ctrigger['AC2']={'use':'Y','mode':1,'st1high':200,'bfsec':0.015,'afsec':120}
config_ctrigger['AC3']={'use':'Y','mode':1,'st1high':200,'bfsec':0.015,'afsec':120}
config_ctrigger['DI']={'use':'Y','mode':3,'st1high':60,'st1low':10}
config_ctrigger['TP']={'use':'Y','mode':3,'st1high':60,'st1low':-20}
config_ctrigger['TI']={'use':'Y','mode':1,'st1high':5}

config_time={'zone':'GMT+9','mode':3,'ip':'time.nist.gov','port':80,'period':600} #600sec

c1={'offset':0,'measureperiod':20,'stateperiod':60,'rawperiod':60}
c2={'st1min':1.01, 'st1max':2.01, 'st2min':3.01, 'st2max':4.01, 'st3min':5.01, 'st3max':6.01, 'st4min':7.01, 'st4max':8.01,
    'st5min':9.01, 'st5max':10.01, 'st6min':11.01, 'st6max':12.01, 'st7min':13.01, 'st7max':14.01, 'st8min':15.01, 'st8max':16.01,
    'st9min':17.01, 'st9max':18.01, 'st10min':19.01, 'st10max':20.01}
config_cmeasure={}
config_cmeasure['AC1']={'sensitivity':20,'samplerate':100,'usefft':'Y'}
config_cmeasure['AC2']={'sensitivity':20,'samplerate':100,'usefft':'Y'}
config_cmeasure['AC3']={'sensitivity':20,'samplerate':100,'usefft':'Y'}
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

state={'battery':0,'memory':0,'disk':0,'cpu':0,'time':'yyyy-MM-dd HH:mm:ss.ffff','uptime':'?days, 13:29:34','abflag':'N','abtime':'','abdesc':'','solarinputvolt':0,'solarinputamp':0,'solarchargevolt':0,'powersupply':0}

ctrl={'cmd':''}
# 'reset','reboot  synctime','fwupdate','realstart','realstop','reqstate','settrigger','settime','setmeasure','setconnect','measurestart','meaurestop'


cse={'name':'cse-gnrb-mon'}
ae={}
ae[F'ae.{bridge}-AC_A1_01_X']={'name':'Accelerator', 'cnt':{'config':{'ctrigger':config_ctrigger['AC1'], 'time':config_time, 'cmeasure':config_cmeasure['AC1'], 'connect':config_connect},
           'info':{'manufacture':info_manufacture['AC1'], 'install':info_install['AC1'],'imeasure':info_imeasure['AC1']},
           'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
           'state':state,
           'ctrl':{"sub":1}}
           }

ae[F'ae.{bridge}-AC_A1_02_X']={'name':'Accelerator', 'cnt':{'config':{'ctrigger':config_ctrigger['AC2'], 'time':config_time, 'cmeasure':config_cmeasure['AC2'], 'connect':config_connect},
           'info':{'manufacture':info_manufacture['AC2'], 'install':info_install['AC2'],'imeasure':info_imeasure['AC2']},
           'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
           'state':state,
           'ctrl':{"sub":1}}
           }

ae[F'ae.{bridge}-AC_A1_03_X']={'name':'Accelerator', 'cnt':{'config':{'ctrigger':config_ctrigger['AC3'], 'time':config_time, 'cmeasure':config_cmeasure['AC3'], 'connect':config_connect},
           'info':{'manufacture':info_manufacture['AC3'], 'install':info_install['AC3'],'imeasure':info_imeasure['AC3']},
           'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
           'state':state,
           'ctrl':{"sub":1}}
           }

ae[F'ae.{bridge}-DI_A1_01_X']={'name':'Displacement Guage', 'cnt':{'config':{'ctrigger':config_ctrigger['DI'], 'time':config_time, 'cmeasure':config_cmeasure['DI'], 'connect':config_connect},
           'info':{'manufacture':info_manufacture['DI'], 'install':info_install['DI'],'imeasure':info_imeasure['DI']},
           'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
           'state':state,
           'ctrl':{"sub":1}}
           }

ae[F'ae.{bridge}-TP_A1_01_X']={'name':'Temperature', 'cnt':{'config':{'ctrigger':config_ctrigger['TP'], 'time':config_time, 'cmeasure':config_cmeasure['TP'], 'connect':config_connect},
           'info':{'manufacture':info_manufacture['TP'], 'install':info_install['TP'],'imeasure':info_imeasure['TP']},
           'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
           'state':state,
           'ctrl':{"sub":1}}
           }

ae[F'ae.{bridge}-TI_A1_01_X']={'name':'Inclinometer', 'cnt':{'config':{'ctrigger':config_ctrigger['TI'], 'time':config_time, 'cmeasure':config_cmeasure['TI'], 'connect':config_connect},
           'info':{'manufacture':info_manufacture['TI'], 'install':info_install['TI'],'imeasure':info_imeasure['TI']},
           'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
           'state':state,
           'ctrl':{"sub":1}}
           }

root='/home/pi/GB'

# mqtt server TOPIC
TOPIC_acc1 = F'/{cse["name"]}/ae.{bridge}-AC_A1_01_X/realtime'
TOPIC_acc2 = F'/{cse["name"]}/ae.{bridge}-AC_A1_02_X/realtime'
TOPIC_acc3 = F'/{cse["name"]}/ae.{bridge}-AC_A1_03_X/realtime'
TOPIC_dis = F'/{cse["name"]}/ae.{bridge}-DI_A1_01_X/realtime'
TOPIC_tem = F'/{cse["name"]}/ae.{bridge}-TP_A1_01_X/realtime'
TOPIC_deg = F'/{cse["name"]}/ae.{bridge}-TI_A1_01_X/realtime'

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
    "acc1":TOPIC_acc1,
    "acc2":TOPIC_acc2,
    "acc3":TOPIC_acc3,
    "dis":TOPIC_dis,
    "tem":TOPIC_tem,
    "deg":TOPIC_deg
    }


if __name__ == "__main__":
    print(ae)
