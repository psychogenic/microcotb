'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from .dut import DUT, Direction

class TTDUT(DUT):
    def __init__(self):
        super().__init__('TTDUT')   
        # call add_rpio with name, direction (in,out or config) and 
        # list of pins
        #  this list looks like verilog order
        #  [ HIGH BIT PIN ... LOW BIT PIN]
        self.add_rpio('ui_in', Direction.INPUT, [3, 4, 15, 17, 2, 14, 18, 27])
        
        # this looks like verilog or a datasheet... now the object has a
        # self.ui_in[7:0]
        # with ui_in[7] coming from pin 3 and input [0] coming from pin 27
        
        
        self.add_rpio('uio', Direction.CONFIGURABLE, [24, 9, 11, 7, 10, 25, 8, 7])
        
        self.add_rpio('uo_out', Direction.OUTPUT, [0, 6, 13, 16, 5, 12, 19, 20])

        # lets say we want a SPI port
        # we could do it individually 
        self.add_rpio('rst_n',  Direction.OUTPUT, 22)
        self.add_rpio('clk', Direction.OUTPUT, 23)
        self.add_rpio('ena', Direction.OUTPUT, 21)

        
        self.uio_out = self.uio 
        self.uio_in = self.uio 
        

        
        
        
        