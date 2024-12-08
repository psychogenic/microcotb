'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb_rpi.dut import DUT, Direction

class Pi5DUT(DUT):
    def __init__(self):
        super().__init__('Pi5DUT')   
        # call add_rpio with name, direction (in,out or config) and 
        # list of pins
        #  this list looks like verilog order
        #  [ HIGH BIT PIN ... LOW BIT PIN]
        self.add_rpio('inputs', Direction.INPUT, [2, 3, 4, 5, 6, 7, 8, 9])
        
        # this looks like verilog or a datasheet... now the object has a
        # self.inputs[7:0]
        # with inputs[7] coming from pin 2 and input [0] coming from pin 9
        
        
        self.add_rpio('outputs', Direction.OUTPUT, [10, 11, 12, 13, 14, 15, 16, 17])
        # could also do a configurable... see the 4-bit SPI port at the bottom
        # self.add_rpio('bidir', Direction.CONFIGURABLE, [18, 19, 20, 21, 22, 23, 24, 25])
        
        
        # lets say we want a SPI port
        # we could do it individually 
        self.add_rpio('cs',  Direction.OUTPUT, 22)
        self.add_rpio('sck', Direction.OUTPUT, 23)
        self.add_rpio('mi',  Direction.INPUT,  24)
        self.add_rpio('mo',  Direction.OUTPUT, 25)
        
        
        # Setup the pins we'll use
        cs, sck, mi, mo = 18, 19, 20, 21
        # pins: CS will be MSB of 4 bit port, SCK is LSB
        # so   [3:0] is:
        pins = [cs, mo, mi, sck]
        self.add_rpio('myspi', Direction.CONFIGURABLE, pins)
        # because we set it CONFIGURABLE, we get an 
        # "oe_myspi" to set output enable on individual bits. 
        # let's set the outputs on for cs, mo and sck
        # notice that it a binary of CS MO MI SCK in that order
        #                         0b  1  1  0  1
        # same as the list of pins
        self.myspi_oe.value = 0b1101
        # you could also do
        # self.oe_myspi.value[3] = 1 to set the CS bit as output
        
        
        
        