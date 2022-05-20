VERSION='2-2_20220519_1755'
print('\n===========')
print(f'Verion {VERSION}')

import os
import sys
import time
from datetime import datetime, timedelta
from RepeatedTimer import RepeatedTimer

import conf

import File_Merge
import File_Cleaner

ae = conf.ae
root=conf.root
priv = datetime.now()

def do_periodic_file(aename):
    global priv
    now = datetime.now()
    print(f"{now.strftime('%H:%M:%S')} +{(now-priv).total_seconds()}s {aename} periodic run uploding raw data files")
    priv=now

    File_Merge.doit(aename)
    File_Cleaner.doit(aename)
    print('----')
	
def run():
    for aename in ae:
        cmeasure=ae[aename]['config']['cmeasure']

        if 'rawperiod' in cmeasure and isinstance(cmeasure['rawperiod'],int): 
            print(f"cmeasure.rawperiod= {cmeasure['rawperiod']} min") 
            interval = cmeasure['rawperiod']
        else: 
            print(f"cmeasure.rawperiod= defauled 60 min") 
            interval = 60

        RepeatedTimer(interval*60, do_periodic_file, aename)


    print('Ready')
    print()

if __name__ == "__main__":
    run()
