
'''
Created on Jan 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import machine
import examples.rp2040.lowlevel_io as lowlevel
import microcotb.dut 
# from examples.rp2040.factory_test import *

class TinyTapeoutDUT(microcotb.dut.DUT):
    def __init__(self, name:str='TinyTapeout'):
        super().__init__(name)
        
        # configuration for all 
        # the I/O in the TT ASICs
        # low-level read/write functions
        # in their own module
        ports = [
              ('uo_out',  8, lowlevel.read_uo_out_byte, None),
              ('ui_in',   8, lowlevel.read_ui_in_byte, 
                               lowlevel.write_ui_in_byte),
              ('uio_in',  8, lowlevel.read_uio_byte, 
                                lowlevel.write_uio_byte),
              ('uio_out', 8, lowlevel.read_uio_byte, None),
              ('uio_oe',  8, lowlevel.read_uio_outputenable, 
                                 lowlevel.write_uio_outputenable)
        ]
        
        # now add a port for each configuration
        for p in ports:
            self.add_port( *p )
        
        # also need clk and reset
        self.clk = PinWrapper('clk', 
                              machine.Pin(0, machine.Pin.OUT))
        self.rst_n = PinWrapper('rst_n', machine.Pin(1, machine.Pin.OUT))
        # ena may be used in existing tests, does nothing
        self.ena = microcotb.dut.NoopSignal('ena', 1)
        # yep, that's it

class PinWrapper(microcotb.dut.PinWrapper):
    def __init__(self, name:str, pin):
        super().__init__(name, pin)
        
    @property 
    def value(self):
        return self._pin.value()
    
    @value.setter 
    def value(self, set_to:int):
        self._pin.value(set_to)
            


    
    