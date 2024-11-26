'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.types.ioport import IOPort
from microcotb.types.handle import LogicObject


class IO(LogicObject):
    def __init__(self, name:str, width:int, read_signal_fn=None, write_signal_fn=None):
        port = IOPort(name, width, read_signal_fn, write_signal_fn)
        super().__init__(port)
        self.port = port
    
    @property 
    def is_readable(self):
        return self.port.is_readable 
    
    @property 
    def is_writeable(self):
        return self.port.is_readable
    
    @property 
    def signal_read(self):
        return self.port.signal_read
    @signal_read.setter 
    def signal_read(self, func):
        self.port.signal_read = func
    @property 
    def signal_write(self):
        return self.port.signal_write
    @signal_write.setter 
    def signal_write(self, func):
        self.port.signal_write = func
        
    
    def __repr__(self):
        val = hex(int(self.value)) if self.port.is_readable  else ''
        return f'<IO {self.port.name} {val}>'
    
    def __str__(self):
        return str(self.value)