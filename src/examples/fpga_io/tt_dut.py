'''
Created on Nov 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.ports.io import IO

# get the Simple USB Bridge DUT
import examples.simple_usb_bridge.dut as sub_dut

import microcotb.log as logging

log = logging.getLogger(__name__)



class TinyTapeoutDUT(sub_dut.DUT):
    '''
        Assume the general purpose AnythingPMOD is loaded with 
        FPGA I/O SUB, with
        
        * clk 
        * rst_n
        * periph1 as an input (reading from demoboard output pmod)
        * periph2 as bidir (read/write from demoboard bidir pmod)
        * host as an output (writing to demoboard input pmod)
        
        We wrap it to give the TT naming ui_in,uio_*,uo_out 
    
    '''
     
    def __init__(self, serial_port:str=sub_dut.DefaultPort, 
                 name:str='FPGA', auto_discover:bool=True):
        super().__init__(serial_port, name, auto_discover)

    def discover(self):
        super().discover()
        # TT ports are named according to the ASIC's 
        # perspective, so we want to provide relevant
        # naming for attributes and
        #  -- read from uo_out 
        #  -- allow user config of uio, default to inputs
        #  -- write to ui_in
        for oeconf in [('periph1', 'uo_out', 0), ('periph2', 'uio', 0), ('host', 'ui_in', 0xff)]:
            oename = f'oe_{oeconf[0]}'
            if hasattr(self, oename):
                log.debug(f'Have oe port for {oeconf[0]}')
                oe_port = getattr(self, oename)
                setattr(self, f'{oeconf[1]}_oe', oe_port)
                log.info(f'Setting {oename} to {hex(oeconf[2])}')
                oe_port.value = oeconf[2]
                
    @property 
    def rst_n(self) -> IO:
        return self.reset
    
    @rst_n.setter 
    def rst_n(self, v:int):
        self.reset.value = v
        
    @property 
    def ui_in(self) -> IO:
        return self.host
    
    @ui_in.setter 
    def ui_in(self, v:int):
        self.host.value = v
    
    @property 
    def uio_in(self) -> IO:
        return self.periph2
    
    @uio_in.setter 
    def uio_in(self, v:int):
        self.periph2.value = v
        
    @property 
    def uio_out(self) -> IO:
        return self.periph2
    
    @property 
    def uo_out(self) -> IO:
        return self.periph1

    
def getDUT(port:str='/dev/ttyACM0'):
    dut = TinyTapeoutDUT(port, 'TT', auto_discover=True)
    return dut