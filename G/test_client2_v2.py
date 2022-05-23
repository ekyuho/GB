import sys
import socket
import json
import time

HOST = '127.0.0.1'      # allow all
if len(sys.argv) != 1:
    PORT = int(sys.argv[1]) # Use PORT <- arguments
else:
    PORT = 50000           # Use PORT <- 50000 (defalut)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

config_data_in_json_str = '{ "ctrigger-ac": { "use": "Y", "mode": 1, "st1high": 200, "st1low": -2000, "bfsec": 30, "afsec": 120 }, "ctrigger-di": { "use": "N", "mode": 3, "st1high": 100, "st1low": 20, "bfsec": 0, "afsec": 0 }, "ctrigger-tp": { "use": "N", "mode": 3, "st1high": 60, "st1low": -20, "bfsec": 0, "afsec": 0 }, "ctrigger-ti": { "use": "N", "mode": 3, "st1high": 5, "st1low": -5, "bfsec": 0, "afsec": 0 },'\
    + '"cmeasure-ac": { "samplerate": 100, "offset": 200, "measureperiod": 600, "stateperiod": 60, "rawperiod": 60 }, "cmeasure-di": { "samplerate": 1, "offset": 200, "measureperiod": 600, "stateperiod": 60, "rawperiod": 60 }, "cmeasure-tp": { "samplerate": 1, "offset": 5, "measureperiod": 600, "stateperiod": 60, "rawperiod": 60 }, "cmeasure-ti": { "samplerate": 1, "offset": 5, "measureperiod": 600, "stateperiod": 60, "rawperiod": 60 } } '

config_str = "CONFIG "+config_data_in_json_str
client_socket.sendall(config_str.encode())
print("Send to Server : CONFIG COMMAND")
time.sleep(1)


print("Received : ")
print(client_socket.recv(1024).decode(), ' \n')

client_socket.close()
