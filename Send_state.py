VERSION='2-2_20220519_1755'
print('\n===========')
print(f'Verion {VERSION}')

from time import process_time
from datetime import datetime, timedelta
from RepeatedTimer import RepeatedTimer

import periodic_state
import conf

broker = conf.host
port = conf.port
ae = conf.ae
root=conf.root

priv = datetime.now()

def do_periodic_state(aename):
    global priv
    now = datetime.now()
    print(f"{now.strftime('%H:%M:%S')} +{(now-priv).total_seconds()}s {aename} periodic run creating state ci")
    priv=now
    periodic_state.update(aename)
    print('----')

def run():
    for aename in ae:
        cmeasure=ae[aename]['config']['cmeasure']

        if 'stateperiod' in cmeasure and isinstance(cmeasure['stateperiod'],int): 
            print(f"cmeasure.stateperiod= {cmeasure['stateperiod']} min")
            interval = cmeasure['stateperiod']
        else: 
            print(f"cmeasure.stateperiod= defaulted 60 min")
            interval = 60

        RepeatedTimer(interval*60, do_periodic_state, aename)


    print('Ready')
    print()

if __name__ == "__main__":
    run()
