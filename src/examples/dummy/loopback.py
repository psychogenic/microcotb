'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.dut import DUT
from microcotb.platform.dummy import PinWrapper
from microcotb.ports.io import IO

class FakePinWithCallback(PinWrapper):
    '''
        A pin that lets us know, through a callback, when 
        it has been set
    '''
    def __init__(self, wr_callback):
        super().__init__()
        self._cb = wr_callback 
    
    @property 
    def value(self):
        return self._value
    @value.setter 
    def value(self, set_to:int):
        self._value = set_to
        self._cb()

class LoopBackCounter(DUT):
    '''
        A (faked) device under test that has
        
            input rst_n, # reset, active low
            input clk, # clock
            input count_en, 
            input [7:0] input,
            output [7:0] output
        
        when reset, output goes to 0
        when count_en is LOW, output matches input (latched on clk high)
        when count_en is HIGH, output is incremented on each clock
    
    '''
    def __init__(self, name:str='LoopBackcount_ener'):
        super().__init__(name)
        self.rst_n = FakePinWithCallback(self.reset_set)
        self.clk = FakePinWithCallback(self.clocked)
        self.count_en = PinWrapper()
        self._input = 0
        self._output = 0
        
        port_defs = [
            ('input',  8, self.read_input_byte, self.write_input_byte),
            ('output', 8, self.read_output_byte, None),
        ]
        for pd in port_defs:
            self.add_port(*pd)
            
    
    def read_input_byte(self):
        return self._input
    
    def write_input_byte(self, val:int):
        self._input = val
        
    def read_output_byte(self):
        return self._output
        
        
    def reset_set(self):
        if not self.rst_n.value:
            self._output = 0
        
    def clocked(self):
        if self.clk.value:
            if not self.rst_n:
                self._output = 0
            else:
                if self.count_en.value:
                    self._output += 1
                else:
                    self._output = self._input
            