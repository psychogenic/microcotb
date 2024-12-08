'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
#from ttboard.demoboard import DemoBoard, Pins
# from ttboard.ports.io import IO
from microcotb.ports.io import IO
import microcotb.log as logging
from microcotb.testcase import TestCase
from microcotb.platform import PinWrapper
from microcotb.types.logic_array import LogicArray

class NoopSignal:
    def __init__(self, name:str, def_value:int=0):
        self._name = name
        self._value = def_value
        
    @property 
    def name(self):
        return self._name 
    @property 
    def value(self):
        return self._value 
    
    @value.setter 
    def value(self, set_to):
        self._value = set_to
        
    def __repr__(self):
        return f'<Noop {self.name}>'
        
class Wire(NoopSignal):
    def __repr__(self):
        return f'<Wire {self.name}>'


class SliceWrapper:
    def __init__(self, name:str, io:IO, idx_or_start:int, slice_end:int=None):
        self._io = io 
        self._name = name
        # can't create slice() on uPython...
        self.slice_start = idx_or_start
        self.slice_end = slice_end
        
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
    
    def __int__(self):
        return int(self.value)
        
            
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


class IOInterface:
    def __init__(self):
        pass 
    
    @classmethod
    def new_slice_attribute(cls, name:str, source:IO, idx_or_start:int, slice_end:int=None):
        return SliceWrapper(name, source, idx_or_start, slice_end)
    
    @classmethod
    def new_bit_attribute(cls, name:str, source:IO, bit_idx:int):
        return SliceWrapper(name, source, bit_idx)
    
    def add_slice_attribute(self, name:str, source:IO, idx_or_start:int, slice_end:int=None):
        slc = self.new_slice_attribute(name, source, idx_or_start, slice_end)
        setattr(self, name, slc)
        return slc
        
    def add_bit_attribute(self, name:str, source:IO, bit_idx:int):
        bt = self.new_bit_attribute(name, source, bit_idx)
        setattr(self, name, bt)
        return bt
        
    def add_port(self, name:str, width:int, reader_function=None, writer_function=None):
        setattr(self, name, IO(name, width, reader_function, writer_function))
    
    def available_io(self):
        # get anything that's IO or IO-based/derived
        return list(filter(lambda x: isinstance(x, (IO, SliceWrapper)), 
                           map(lambda a: getattr(self, a), 
                               filter(lambda g: not g.startswith('_'), 
                                      sorted(dir(self))))))
    
    
    def __setattr__(self, name:str, value):
        if hasattr(self, name) and isinstance(getattr(self, name), (IO, SliceWrapper)):
            port = getattr(self, name)
            port.value = value 
            return
        super().__setattr__(name, value)
          
class DUT(IOInterface):
    def __init__(self, name:str='DUT'):
        self.name = name
        self._log = logging.getLogger(name)
        
        
    def testing_will_begin(self):
        # override if desired
        pass
    def testing_unit_start(self, test:TestCase):
        # override if desired
        pass
    def testing_unit_done(self, test:TestCase):
        # override if desired
        pass 
    
    def testing_done(self):
        # override if desired
        pass
    
        
        
    
        
        
