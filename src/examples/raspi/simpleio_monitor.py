'''
Created on Dec 8, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb_rpi import SimpleIO, Direction, StateChangeReport


import time
import logging
logging.basicConfig(level=logging.INFO)

# Could use a class, but we're just going to build it up live

# construct the object, we're going to snoop at stuff
# happening live on a TT demoboard, from the raspberry pi
# wired up to it
pi = SimpleIO('demoboard')

# there's a clock pin in there
pi.add_rpio('clk', Direction.INPUT, 23)

# the demoboard push data onto the ASIC input 
# through here
pi.add_rpio('asic_in', Direction.INPUT, [3, 4, 15, 17, 2, 14, 18, 27])

# the ASIC outputs results on this port
pi.add_rpio('asic_out', Direction.INPUT, [0, 6, 13, 26, 5, 12, 19, 20])


# lets make it easy to see the MSB
# with this, we'll have a pi.msb which is the same as pi.asic_out[7]
# but we can trigger callbacks on changes to it
# and we could write to it easily as pi.msb = 1, if it was an output
pi.add_bit_attribute('msb', pi.asic_out, 7)

# and the low nibble.  Notice this is asic_out[3:0] -- like in a datasheet
pi.add_slice_attribute('nibble', pi.asic_out, 3, 0)

# also a bidirectional port

# this one is configurable, but it starts off as all inputs
pi.add_rpio('bidir', Direction.CONFIGURABLE, [24, 9, 11, 1, 10, 25, 8, 7])

# there's a global state change callback you can use
# but there are some convenience methods to watch 
# for specific things.  We'll use those
# 
# Lets create some callbacks to track things.
# these all have the same signature:
#  func( NAME, VALUE, REPORT)
# with
#  NAME: the I/O port or bit or slice that triggered it
#  VALUE: the current value of the bit/slice/port
#  REPORT: the entire StateChangeReport if you care 
#  about other things that may have changed along with it.
class StateTracker:
    ClockCount = 0
    nibble = 0
    
def clock_count(name:str, value:int, report:StateChangeReport):
    # this will go fast, so we just
    StateTracker.ClockCount += 1
    

def print_data(name:str, value:int, report:StateChangeReport):
    if name == 'nibble':
        print(f'Our nibble is now {value:04b} ({value})')
        StateTracker.nibble = value
        if report.has('msb'):
            print(f'MSB changed at the same time!')
    else:
        print(f'Value for {name} is {value}')


# specify a few callbacks for different things
pi.watch_for_state('clk', clock_count)
pi.watch_for_state('nibble', print_data)
pi.watch_for_state('msb', print_data)



def poll_loop():
    # now tell the we want to generate reports
    # this is also used when dumping VCDs and such
    pi.is_monitoring = True
    while True:
        pi.poll_for_input_events()
        #time.sleep(0.0005) # don't go nutz

