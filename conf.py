#host="m.damoa.io"
host="218.232.234.232"  #건교부 테스트 사이 
port=1883

cse={'name':'cse-gnrb-mon'}
bridge='025742'  #교량코드
ae={}
cnt_proto={'config':{'ctrigger':{},'time':{},'cmeasure':{},'connect':{}},
           'info':{'manufacture':{}, 'install':{},'imeasure':{}},
           'data':{'dtrigger':{},'fft':{},'dmeasure':{}},
           'state':{},
           'ctrl':{"sub":1}}
ae[F'ae.{bridge}-AC_A1_01_X']={'name':'Accelerator', 'cnt':cnt_proto}
ae[F'ae.{bridge}-AC_A1_02_X']={'name':'Accelerator', 'cnt':cnt_proto}
ae[F'ae.{bridge}-AC_A1_03_X']={'name':'Accelerator', 'cnt':cnt_proto}
ae[F'ae.{bridge}-DI_A1_01_X']={'name':'Displacement Guage', 'cnt':cnt_proto}
ae[F'ae.{bridge}-TP_A1_01_X']={'name':'Temperature', 'cnt':cnt_proto}
ae[F'ae.{bridge}-TI_A1_01_X']={'name':'Inclinometer', 'cnt':cnt_proto}

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
