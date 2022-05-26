# Send_data.py
VERSION='2-2_20220519_1755'
print('\n===========')
print(f'Verion {VERSION}')

import os
import sys
import time
from time import process_time
from datetime import datetime, timedelta
from RepeatedTimer import RepeatedTimer

import periodic_acceleration
import periodic_temperature
import periodic_degree
import periodic_displacement
import create  #for Mobius resource
import conf

ae = conf.ae
priv = datetime.now()

def sensor_type(aename):
	return aename.split('-')[1][0:2]

# handles periodic measure (fft for AC)
def do_periodic_data(aename):
	global ae, priv
	if ae[aename]['local']['measurestart']=='N':  # measure is controlled from remote user
		print('measurestart==N, skip periodic data sending')
		return

	now = datetime.now()
	print(f"{now.strftime('%H:%M:%S')} +{(now-priv).total_seconds()}s {aename} periodic run creating data ci")
	priv=now
	stype = sensor_type(aename)
	if stype=='AC': 
		periodic_acceleration.report(aename)
	elif stype=='DI':
		periodic_displacement.report(aename)
	elif stype=='TI':
		periodic_degree.report(aename)
	elif stype=='TP':
		periodic_temperature.report(aename)
	print('----')
	
def run():
	for aename in ae:
		cmeasure=ae[aename]['config']['cmeasure']
	
		if 'measureperiod' in cmeasure and isinstance(cmeasure['measureperiod'],int): 
			print(f"cmeasure.measureperiod= {cmeasure['measureperiod']} sec") 
			interval = cmeasure['measureperiod']
		else: 
			print(f"cmeasure.measureperiod= defaulted 600 sec") 
			interval = 600
		RepeatedTimer(interval, do_periodic_data, aename)

		print(f"{aename} cmeasure.usefft= {cmeasure['usefft']}") 
		print(f"{aename} ctrigger.use= {ae[aename]['config']['ctrigger']['use']}") 
		print(f"{aename} measurestart= {ae[aename]['local']['measurestart']}")
	print('Ready')
	print()

if __name__ == '__main__':
	run()
