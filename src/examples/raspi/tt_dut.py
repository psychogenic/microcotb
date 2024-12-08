'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb_rpi.dut import DUT, Direction

class TinyTapeoutDUT(DUT):
    '''
        With TinyTapeout demoboards, names are 
        
            FROM THE PERSPECTIVE OF THE ASIC
        
        so ui_in -- is input to the ASIC, so we will be writing to it, etc.
    
    '''
    def __init__(self, name:str='TTDUT'):
        super().__init__(name)   
        # call add_rpio with name, direction (in,out or config) and 
        # list of pins
        #  this list looks like verilog order
        #  [ HIGH BIT PIN ... LOW BIT PIN]
        self.add_rpio('ui_in', Direction.OUTPUT, [3, 4, 15, 17, 2, 14, 18, 27])
        
        # this looks like verilog or a datasheet... now the object has a
        # self.ui_in[7:0]
        # with ui_in[7] coming from pin 3 and input [0] coming from pin 27
        self.add_rpio('uio', Direction.CONFIGURABLE, [24, 9, 11, 1, 10, 25, 8, 7])
        
        self.add_rpio('uo_out', Direction.INPUT, [0, 6, 13, 26, 5, 12, 19, 20])

        # lets say we want a SPI port
        # we could do it individually 
        self.add_rpio('rst_n',  Direction.OUTPUT, 22)
        self.add_rpio('clk', Direction.OUTPUT, 23)
        self.add_rpio('ena', Direction.OUTPUT, 21)

        
        self.uio_out = self.uio 
        self.uio_in = self.uio 
        

        
        
        
        