'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.platform.features import Features
from time import *
if not Features.SleepMsUs:
    def sleep_ms(v):
        sleep(v/1000)

    def sleep_us(v):
        sleep(v/1000000)

if not Features.TicksUs:
    def ticks_us():
        return int(time())
