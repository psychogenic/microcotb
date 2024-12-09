'''
Created on Dec 8, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.ports.io import IO
from microcotb.types.logic_array import LogicArray
from microcotb.types.with_value import WithValue

class NoopSignal(WithValue):
    def __init__(self, name:str, def_value:int=0):
        super().__init__(def_value)
        self._name = name
        
    @property 
    def name(self):
        return self._name 
            
    def __repr__(self):
        return f'<Noop {self.name}>'
        
class Wire(NoopSignal):
    def __repr__(self):
        return f'<Wire {self.name}>'


class SliceWrapper(WithValue):
    def __init__(self, name:str, io:IO, idx_or_start:int, slice_end:int=None):
        super().__init__()
        self._io = io 
        self._name = name
        # can't create slice() on uPython...
        self.slice_start = idx_or_start
        self.slice_end = slice_end
        
    def __hash__(self)->int:
        return hash(f'{self._name}{self.slice_start}{self.slice_end}')
    def out_of_array(self, la:LogicArray) -> LogicArray:
        if self.slice_end is not None:
            v = la[self.slice_start:self.slice_end]
        else:
            v = la[self.slice_start]
        return v
    
    
    @property 
    def value(self):
        if self.slice_end is not None:
            return self._io[self.slice_start:self.slice_end]
        
        return self._io[self.slice_start]
    
    @value.setter 
    def value(self, set_to:int):
        if self.slice_end is not None:
            self._io[self.slice_start:self.slice_end] = set_to
        else:
            self._io[self.slice_start] = set_to
            
    @property 
    def is_readable(self):
        return self._io.is_readable
    
    @property 
    def is_writeable(self):
        return self._io.is_writeable
    
    @property 
    def name(self):
        return self._name
    
    @property 
    def width(self):
        if self.slice_end is not None:
            return (self.slice_start - self.slice_end) + 1
        return 1

    def _get_item_keys(self, key):
        if isinstance(key, int):
            return [key + self.slice_end]
        elif isinstance(key, slice):
            # going to assume we have a slice_end or just barf
            end = self.slice_end + key.stop if key.stop is not None else None 
            start = self.slice_end + key.start if key.start is not None else None
            return [start, end]
        
        return []
        
    def __setitem__(self, key, val):
        keys = self._get_item_keys(key)
        if len(keys) == 1:
            self._io[keys[0]] = val
        elif len(keys) == 2:
            self._io[keys[0]:keys[1]] = val

    
    def __getitem__(self, key):
        keys = self._get_item_keys(key)
        if len(keys) == 1:
            return self.value[keys[0]]
        elif len(keys) == 2:
            return self.value[keys[0]:keys[1]]
        return None
    
    def __len__(self):
        if self.slice_end is None:
            return 1
        return len(self.value)
            
    def __repr__(self):
        nm = self._io.port.name 
        if self.slice_end is not None:
            return f'<Slice {self._name} {nm}[{self.slice_start}:{self.slice_end}] ({hex(self.value)})>'
        return f'<Slice {self._name} {nm}[{self.slice_start}] ({hex(self.value)})>'
        
    def __str__(self):
        if self.slice_end is not None:
            return str(self._io[self.slice_start:self.slice_end])
        else:
            return str(self._io[self.slice_start])

