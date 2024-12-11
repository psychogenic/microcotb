'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.ports.io import IO
import microcotb.log as logging
from microcotb.testcase import TestCase

from microcotb.sub_signals import SliceWrapper

# import these here so users don't need to go 
# hunting for them in the lib
from microcotb.platform import PinWrapper
from microcotb.sub_signals import NoopSignal, Wire


class IOInterface:
    def __init__(self):
        self._avail_io = [] 
    
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
        
    def add_port(self, name:str, width:int, reader_function=None, writer_function=None, initial_value=None):
        io = IO(name, width, reader_function, writer_function)
        setattr(self, name, io)
        if initial_value is not None:
            io.value = initial_value
    
    def available_io(self, types_of_interest=None):
        # get anything that's IO or IO-based/derived
        if self._avail_io is None:
            # do a search
            self._avail_io = \
                list(filter(lambda x: isinstance(x, (IO, SliceWrapper)), 
                               map(lambda a: getattr(self, a), 
                                   filter(lambda g: not g.startswith('_'), 
                                          sorted(dir(self))))))
        if types_of_interest is None:
            return self._avail_io
        
        return list(filter(lambda x: isinstance(x, types_of_interest), self._avail_io))
    
    def available_ports(self):
        '''
            Available IO source ports, ie. IO objects, not 
            slice/bit aliasing
        '''
        return self.available_io((IO,))
    
    def __setattr__(self, name:str, value):
        if hasattr(self, name):
            port = getattr(self, name)
            if isinstance(port, (IO, SliceWrapper)):
                port.value = value 
                return
        elif isinstance(value, (IO, SliceWrapper)):
            # don't know this yet, and it's IO
            if hasattr(self, '_avail_io'):
                self._avail_io.append(value)
        
        super().__setattr__(name, value)
        
    



class DUT(IOInterface):
    def __init__(self, name:str='DUT'):
        super().__init__()
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
    
        
        
    
    def __repr__(self):
        availNames = []
        for io in self.available_io():
            availNames.append(io.name)
        if not len(availNames):
            return f'<DUT {self.name}>'
        return f'<DUT {self.name} ({",".join(availNames)})>'
    
        
        
