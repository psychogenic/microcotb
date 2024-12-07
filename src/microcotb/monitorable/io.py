'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.ports.io import IO
class MonitorableIO(IO):
    
    def __init__(self, name:str, width:int, read_signal_fn=None, write_signal_fn=None):
        def rd_cb_trigger():
            v = read_signal_fn()
            cb = self._read_notif_callback
            if cb is not None:
                cb(self, v)
            return v
            
        def wr_cb_trigger(val):
            ret = write_signal_fn(val)
            cb = self._write_notif_callback
            if cb is not None:
                cb(self, val)
            return ret 
                
        
        super().__init__(name, width, 
                         rd_cb_trigger if read_signal_fn is not None else None, 
                         wr_cb_trigger if write_signal_fn is not None else None)
        
        self._write_notif_callback = None
        self._read_notif_callback = None
        
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