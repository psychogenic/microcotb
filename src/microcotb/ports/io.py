'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.types.ioport import IOPort
from microcotb.types.handle import LogicObject
from microcotb.types.logic_array import LogicArray


class IO(LogicObject):
    _IOPORT_COUNT = 0
    
    def __init__(self, name:str, width:int, read_signal_fn=None, write_signal_fn=None):
        port = IOPort(name, width, read_signal_fn, write_signal_fn)
        super().__init__(port)
        self.port = port
        self._hashval = None
        self._ioidx = IO._IOPORT_COUNT
        IO._IOPORT_COUNT += 1
        
        
    def __hash__(self): 
        if self._hashval is None:
            self._hashval = hash(f'{self.port.name}-{self._ioidx}')
        return self._hashval
        
    @property 
    def last_value(self) -> int:
        return self.port.last_value
    
    @property
    def last_value_as_array(self) -> LogicArray:
        return LogicArray._from_handle(self.port.last_value_bin_str)
    
    def value_as_array(self, v:int) -> LogicArray:
        return LogicArray._from_handle(self.port.last_value_bin_str)
    
    @property 
    def is_readable(self) -> bool:
        return self.port.is_readable 
    
    @property 
    def is_writeable(self) -> bool:
        return self.port.is_readable
    
    @property 
    def width(self) -> int:
        return self.port.width
    
    @property 
    def max_value(self) -> int:
        return (2**self.port.width)-1
    
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
        
    @property 
    def name(self) -> str:
        return self.port.name
        
    def invert(self):
        self.value = ~self 
        
    def clock(self, n_times:int=1):
        for _i in range(n_times):
            self.invert()
            self.invert()
    def __repr__(self):
        val = hex(int(self.value)) if self.port.is_readable  else ''
        return f'<IO {self.name} {val}>'
    
    def __int__(self):
        if self.port.is_readable:
            return int(self.value)
        return None
    
    
    def __invert__(self):
        mv = self.max_value
        return ~(mv & int(self)) & mv
    
    def __str__(self):
        return str(self.value)
