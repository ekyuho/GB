import requests
import json
import random
import time
from paho.mqtt import client as mqtt_client

import conf
host = conf.host
port = conf.port
bridge = conf.bridge
cse = conf.cse
ae = conf.ae

root=conf.root

client_id = f'python-mqtt-{random.randint(0, 1000)}'

flag_connected = 0
TOPIC="/oneM2M/req/cse-gnrb-mon/#"

def gotit(topic, msg):
    print(topic, msg)

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print(f"Connected to {host} via MQTT")
            global flag_connected
            flag_connected = 1
            if TOPIC != "":
                client.subscribe(TOPIC)
                print("subscribed to {}".format(TOPIC))
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_disconnect(client, userdata, rc):
        global flag_connected
        flag_connected = 0
        print("Disconnected from MQTT Broker!")

    def on_message(client, _topic, _msg):
        topic=_msg.topic.split('/')
        msg=_msg.payload.decode('utf8')
        ts = time.strftime('%I:%M:%S', time.localtime())
        gotit(topic, msg)
            
    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    if flag_connected == 0:
        client.connect(host, port)
    return client

client = connect_mqtt()
client.loop_forever()

