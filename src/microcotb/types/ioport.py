'''
Created on Nov 20, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.types.range import Range
import microcotb.log as logging
log = logging.getLogger(__name__)

class Port:    
    def __init__(self, name:str, width:int, read_signal_fn=None, write_signal_fn=None):
        self.name = name 
        self.width = width
        self.signal_read = read_signal_fn 
        self.signal_write = write_signal_fn
    
    @property 
    def is_readable(self):
        return self.signal_read is not None 
    
    @property 
    def is_writeable(self):
        return self.signal_write is not None 
        
    def set_signal_val_int(self, vint:int):
        if self.signal_write is None:
            log.error(f'writes not supported on {self.name}')
            return
        self.signal_write(vint)
        
    def set_signal_val_binstr(self, vstr:str):
        if self.signal_write is None:
            log.error(f'writes not supported on {self.name}')
            return 
        self.signal_write(int(vstr, 2))
        
        
    def get_signal_val_binstr(self):
        if self.signal_read is None:
            log.error(f'reads not supported on {self.name}')
            return
        val = self.signal_read()
        fstr = '{v:0' + str(self.width) + 'b}'
        return fstr.format(v=val)
    
    def get_name_string(self):
        return self.name
    
    def get_type_string(self):
        return 'byte' # not sure what to return here
    
    def get_definition_name(self):
        return self.get_name_string()
    
    def get_range(self):
        return (self.width-1, 0, Range.RANGE_DOWN)
    
    def get_const(self) -> bool:
        return False
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Port):
            return NotImplemented
        return self.signal_read() == other.signal_read()
    
    


class IOPort(Port):
    pass
