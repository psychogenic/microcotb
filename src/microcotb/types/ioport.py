'''
Created on Nov 20, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.types.range import Range
import microcotb.log as logging
import microcotb.utils.tm as time
from microcotb.types.logic_array import LogicArray
log = logging.getLogger(__name__)

RangeDirection = Range.RANGE_DOWN
def set_range_direction_verilog():
    global RangeDirection
    RangeDirection = Range.RANGE_DOWN
def set_range_direction_python():
    global RangeDirection
    RangeDirection = Range.RANGE_UP
    
def range_direction_is_verilog():
    global RangeDirection
    return RangeDirection == Range.RANGE_DOWN
DefaultResilientDebounceTries = 0
DefaultDebounceUSecs = 0
    
class Port:
    
    def __init__(self, name:str, width:int, read_signal_fn=None, write_signal_fn=None):
        self.name = name 
        self.width = width
        self.signal_read = read_signal_fn 
        self.signal_write = write_signal_fn
        self._last_value = 0
        self._fstr = '{v:0' + str(self.width) + 'b}'
        self.resilientDebounceTries = DefaultResilientDebounceTries
        self.debounceUSecs = DefaultDebounceUSecs
    
    @property 
    def last_value(self) -> int:
        return self._last_value
    
    
    @property 
    def last_value_bin_str(self):
        return self._fstr.format(v=self._last_value)
    
    def value_as_bin_str(self, v:int):
        s = self._fstr.format(v=v)
        # print(f'FMT {self._fstr} and {v} and {s}')
        return s
    
    def value_as_array(self, v:int) -> LogicArray:
        return LogicArray._from_handle(self.value_as_bin_str(v))
    
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
        self.do_write(vint)
        
    def set_signal_val_binstr(self, vstr:str):
        if self.signal_write is None:
            log.error(f'writes not supported on {self.name}')
            return 
        vint = int(vstr, 2)
        self.do_write(vint)
        
        
    def get_signal_val_binstr(self):
        if self.signal_read is None:
            log.error(f'reads not supported on {self.name}')
            return
        val = self.do_read()
        fstr = '{v:0' + str(self.width) + 'b}'
        return fstr.format(v=val)
    
    def get_name_string(self):
        return self.name
    
    def get_type_string(self):
        return 'byte' # not sure what to return here
    
    def get_definition_name(self):
        return self.get_name_string()
    
    def get_range(self):
        global RangeDirection
        if RangeDirection == Range.RANGE_DOWN:
            return (self.width-1, 0, RangeDirection)
        return (0, self.width-1, Range.RANGE_UP)
        
    
    def get_const(self) -> bool:
        return False
        
    def __eq__(self, other) -> bool:
        if not isinstance(other, Port):
            return NotImplemented
        return self.signal_read() == other.signal_read()
    
    def _do_read_resilient(self):
        attempt = 0
        vo = list(range(self.resilientDebounceTries))
        while vo.count(vo[0]) != len(vo):
            if attempt:
                if attempt > 1:
                    log.info(f'resilient read {attempt} times (last {vo})')
                else:
                    log.debug(f'resilient read {attempt} times (last {vo})')
            attempt += 1
            for a in range(self.resilientDebounceTries):
                vo[a] = self.signal_read()            
                time.sleep(self.debounceUSecs/(2*1e6))
                
        return vo[0]
    
    def do_read(self):
        if self.resilientDebounceTries:
            self._last_value = self._do_read_resilient()
        else:
            self._last_value = self.signal_read()
        return self._last_value 
    def do_write(self, v):
        self._last_value = v
        self.signal_write(v)
        # print(f"WCH {self._last_value}")
    def do_force_update_last_value(self, v):
        # only for subclasses
        self._last_value = v


class IOPort(Port):
    pass
