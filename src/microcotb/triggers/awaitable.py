'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import microcotb.log as logging 

class Awaitable:
    def __init__(self, signal=None):
        self.signal = signal
        self._log = None
    
    @property 
    def logger(self):
        if self._log is None:
            self._log = logging.getLogger(str(self))
            
        return self._log
            
    def __iter__(self):
        return self

    def __next__(self): 
        raise StopIteration
    
    def __str__(self):
        return f'<Awaitable>'