#!/usr/bin/env python3

import anthemav
import asyncore
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

a = anthemav.AnthemAVR()
a.doconnect('172.28.0.92',14999)
a.turn_on()

while True:
    if a.connected == False:
        a.doconnect('172.28.0.92',14999)
    asyncore.loop(timeout=1, count=15)
    a.query('Z1POW')
    print('Power State is '+str(a.power))
    print('Muted State is '+str(a.muted))
    print('Attenuation is '+str(a.attenuation))
    print('Volume is '+str(a.volume))
    print('Raw is '+str(a.rawvalue))
    print('-- ')
