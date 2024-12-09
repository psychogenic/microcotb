'''
Created on Dec 8, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import logging
import time
logging.basicConfig(level=logging.INFO)
from microcotb_rpi import *

def something_changed(ho):
    print(str(ho))

pi = SimpleIO('hoho', something_changed)
pi.add_rpio('asic_in', Direction.INPUT, [3, 4, 15, 17, 2, 14, 18, 27], initial_value=0)


#print(f"\n\nOut value started at {pi.out.value}, setting to 0xff")
#pi.out = 0xff


pi.add_rpio('asic_out', Direction.INPUT, [0, 6, 13, 26, 5, 12, 19, 20])
pi.add_bit_attribute('msb', pi.asic_out, 7)
pi.add_bit_attribute('inter', pi.asic_out, 5)
# pi.add_slice_attribute('count', pi.asic_out, 4, 0)

pi.add_rpio('bidir', Direction.CONFIGURABLE, [24, 9, 11, 1, 10, 25, 8, 7])


pi.is_monitoring = True


while True:
   pi.poll_for_input_events()
   time.sleep(0.0005)

