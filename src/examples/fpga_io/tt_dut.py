'''
Created on Nov 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.ports.io import IO

# get the Simple USB Bridge DUT
import examples.simple_usb_bridge.dut_sub as dut_sub

import microcotb.log as logging

log = logging.getLogger(__name__)

class NoopSignal:
    def __init__(self, name:str):
        self.name = name 
        self.value = 0

class TinyTapeoutDUT(dut_sub.DUT):
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
     
    def __init__(self, serial_port:str=dut_sub.DefaultPort, 
                 name:str='FPGA', auto_discover:bool=True,
                 start_readonly:bool=False):
        self.start_readonly = start_readonly
        super().__init__(serial_port, name, auto_discover)
        if not hasattr(self, 'ena'):
            self.ena = NoopSignal('ena') # give it a default 'ena' that does nothing
        
    def discover(self):
        super().discover()
        # TT ports are named according to the ASIC's 
        # perspective, so we want to provide relevant
        # naming for attributes and
        #  -- read from uo_out 
        #  -- allow user config of uio, default to inputs
        #  -- write to ui_in
        
        aliases = [
                ('periph1', 'uo_out'),
                ('periph2', 'uio'),
                ('host', 'ui_in'),
                ('reset', 'rst_n'),
            ]
        
        for al in aliases:
            if hasattr(self, al[0]):
                self.alias_signal(al[1], getattr(self, al[0]))
        
        if self.start_readonly:
            ui_in_oe_set = 0
        else:
            ui_in_oe_set = 0xff
        for oeconf in [('periph1', 'uo_out', 0), ('periph2', 'uio', 0), ('host', 'ui_in', ui_in_oe_set)]:
            oename = f'oe_{oeconf[0]}'
            if hasattr(self, oename):
                log.debug(f'Have oe port for {oeconf[0]}')
                oe_port = getattr(self, oename)
                self.alias_signal(f'{oeconf[1]}_oe', oe_port)
                log.info(f'Setting {oename} to {hex(oeconf[2])}')
                oe_port.value = oeconf[2]
                
                
        
                
    @property 
    def uio_in(self) -> IO:
        if not hasattr(self, 'uio'):
            return None
        return self.uio
    
    @uio_in.setter 
    def uio_in(self, v:int):
        self.uio.value = v
        
    @property 
    def uio_out(self) -> IO:
        if not hasattr(self, 'uio'):
            return None
        return self.uio
    

    
def getDUT(port:str='/dev/ttyACM0', start_readonly:bool=False):
    dut = TinyTapeoutDUT(port, 'TT', auto_discover=True, start_readonly=start_readonly)
    return dut
