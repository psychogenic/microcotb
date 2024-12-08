'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.ports.io import IO
class MonitorableIO(IO):
    
    def __init__(self, name:str, width:int, read_signal_fn=None, write_signal_fn=None):
        super().__init__(name, width, 
                         self.wrapped_signal_read if read_signal_fn is not None else None,
                         self.wrapped_signal_write if write_signal_fn is not None else None)
        
        self._orig_signal_read_fn = read_signal_fn
        self._orig_signal_write_fn = write_signal_fn
        
        
        self._write_notif_callback = None
        self._read_notif_callback = None
        
    
    @property
    def signal_read(self):
        return self.wrapped_signal_read
    
    @signal_read.setter 
    def signal_read(self, set_to):
        self.port.signal_read = set_to 
        
        
    @property
    def signal_write(self):
        return self.wrapped_signal_write
    
    @signal_write.setter 
    def signal_write(self, set_to):
        self.port.signal_write = set_to 
    
        
    @property 
    def read_notifications_to(self):
        return self._read_notif_callback
        
    @read_notifications_to.setter 
    def read_notifications_to(self, cb):
        self._read_notif_callback = cb
        
    @property 
    def write_notifications_to(self):
        return self._write_notif_callback
        
    @write_notifications_to.setter 
    def write_notifications_to(self, cb):
        self._write_notif_callback = cb
        
        
    def wrapped_signal_read(self):
        v = self._orig_signal_read_fn()
        cb = self.read_notifications_to
        if cb is not None:
            # print("Calling rd notif")
            cb(self, v)
        return v
            
    def wrapped_signal_write(self, val):
        ret = self._orig_signal_write_fn(val)
        cb = self.write_notifications_to
        if cb is not None:
            #print("Calling wr notif")
            cb(self, val)
        return ret 