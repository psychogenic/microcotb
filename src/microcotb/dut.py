'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
#from ttboard.demoboard import DemoBoard, Pins
# from ttboard.ports.io import IO
from microcotb.ports.io import IO
import microcotb.log as logging
from microcotb.platform import PinWrapper

class NoopSignal:
    def __init__(self, def_value:int=0):
        self._value = def_value
        
    @property 
    def value(self):
        return self._value 
    
    @value.setter 
    def value(self, set_to):
        self._value = set_to
        
class Wire(NoopSignal):
    pass


class SliceWrapper:
    def __init__(self, port, idx_or_start:int, slice_end:int=None):
        self._port = port 
        # can't create slice() on uPython...
        self.slice_start = idx_or_start
        self.slice_end = slice_end
        
    @property 
    def value(self):
        if self.slice_end is not None:
            return self._port[self.slice_start:self.slice_end]
        
        return int(self._port[self.slice_start])
    
    @value.setter 
    def value(self, set_to:int):
        if self.slice_end is not None:
            self._port[self.slice_start:self.slice_end] = set_to
        else:
            self._port[self.slice_start] = set_to
    def __int__(self):
        return int(self.value)
    def __repr__(self):
        if self.slice_end is not None:
            return str(self._port[self.slice_start:self.slice_end])
        else:
            return str(self._port[self.slice_start])


            

class DUTWrapper:
    def __init__(self, name:str='DUT'):
        self.name = name
        self._log = logging.getLogger(name)
        
        
    def testing_will_begin(self):
        pass
        
    @classmethod
    def new_slice_attribute(cls, source:IO, idx_or_start:int, slice_end:int=None):
        return SliceWrapper(source, idx_or_start, slice_end)
    
    @classmethod
    def new_bit_attribute(cls, source:IO, bit_idx:int):
        return SliceWrapper(source, bit_idx)
    
    def add_slice_attribute(self, source:IO, name:str, idx_or_start:int, slice_end:int=None):
        slc = self.new_slice_attribute(source, idx_or_start, slice_end)
        setattr(self, name, slc)
        
        
    def add_port(self, name:str, width:int, reader_function=None, writer_function=None):
        setattr(self, name, IO(name, width, reader_function, writer_function))
        
class DUT(DUTWrapper):
    
    def __init__(self, name:str='DUT'):
        super().__init__(name)
        
        
    
        
        