'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
'''
Created on Dec 5, 2024

Baseclass for "monitorable" DUTs.
If we have a DUT we can monitor--i.e. get notifications about 
changes to signals of interest--then we have what we need to
keep track of these and write out VCD files.

This baseclass handles all this in an abstract way... just how you 
are monitoring and adding events to the queue is up to implementation
class, but if you can do that, then the VCD-related attributes will
handle all the details behind the scenes, in here.

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.ports.io import IO
from microcotb_sub.signal import Signal


class SUBIO(IO):
    '''
        Derive from IO, mostly to implement our between-test reset() optimization
    '''
    def __init__(self, sig:Signal, name:str, width:int, read_signal_fn=None, write_signal_fn=None):
        super().__init__(name, width, read_signal_fn, write_signal_fn)
        self._sub_signal = sig
        
    
    def reset(self):
        self._sub_signal.reset()
        
    @property
    def is_writeable(self) -> bool:
        return self._sub_signal.is_writeable
    
    
    def toggle(self):
        if int(self.value):
            self.value = 1
        else:
            self.value = 0
            
    def clock(self, num_times:int = 1):
        for _i in range(num_times):
            self.toggle()
            self.toggle()
