'''
Created on Nov 28, 2024

SUB-independant base classes.  Most of what we need to implement a
Simple USB Bridge, but without the details of the actual serial
port and protocol.  

This should make it easy to implement better protocols.

@see: dut_sub.py for the implementation I have running

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import os 
from microcotb.ports.io import IO

import microcotb.log as logging
import microcotb.dut 
from microcotb.monitorable.dut import MonitorableDUT, StateChangeReport
from microcotb_sub.signal import Signal

log = logging.getLogger(__name__)



class SUBIO(IO):
    '''
        Derive from IO, mostly to implement our between-test reset() optimization
    '''
    def __init__(self, sig:Signal, name:str, width:int, read_signal_fn=None, write_signal_fn=None):
        super().__init__(name, width, read_signal_fn, write_signal_fn)
        self._sub_signal = sig
        
    @property 
    def signal(self) -> Signal:
        return self._sub_signal
    
    @property 
    def name(self) -> str:
        return self.port.name 
    
    @property 
    def width(self) -> int:
        return self.port.width
    
    def reset(self):
        self.signal.reset()
        
    @property
    def is_writeable(self) -> bool:
        return self.signal.is_writeable
    
    
    def toggle(self):
        if int(self.value):
            self.value = 1
        else:
            self.value = 0
            
    def clock(self, num_times:int = 1):
        for _i in range(num_times):
            self.toggle()
            self.toggle()

class DUT(MonitorableDUT):
    '''
        A DUT base class that allows for auto-discovery, tracking state changes
        (for VCD) and writing VCD output for tests, aliasing signals, etc.
    '''
    def __init__(self, 
                 name:str='SUB', 
                 auto_discover:bool=False):
        super().__init__(name)
        self._added_signals = dict()
        self._signal_by_address = dict()
        self._alias_to_signal = dict()
        self._signal_name_to_alias = None
        
        if auto_discover:
            self.discover()
    
    def add_signal(self, name, addr, width:int, is_writeable_input:bool=False):
        log.error("Override add_signal")
        raise RuntimeError('add_signal needs override')
        return 
    
    def discover(self):
        log.error('override discover')
        raise RuntimeError('discover needs override')
        return
    
    
    def vcd_initial_state_reports(self) -> StateChangeReport:
        stateChange = StateChangeReport()
        
        for signame in self._added_signals.keys():
            if self.has_alias_for(signame):
                continue #skip aliase
            s = self._added_signals[signame]
            log.debug(f"Current state {signame} = {s.value}")
            stateChange.add_change(signame, s.value)
        
        if len(stateChange):
            return [stateChange]
        return []
                
            
    
    
    def testing_will_begin(self):
        # you might wish to override this
        super().testing_will_begin()
                
    def testing_unit_start(self, test:microcotb.dut.TestCase):
        # you might wish to override this
        super().testing_unit_start(test)
                
            
    
    def testing_unit_done(self, test:microcotb.dut.TestCase):
        for s in self._added_signals.values():
            s.reset()
        
        super().testing_unit_done(test)
         
    
    def alias_signal(self, name:str, s:Signal):
        setattr(self, name, s)
        self._added_signals[name] = s
        self._alias_to_signal[name] = s
        self._signal_name_to_alias = None
        
    def aliased_name_for(self, signal_name:str):
        if self._signal_name_to_alias is None:
            self._signal_name_to_alias = dict()
            for alname,sig in self._alias_to_signal.items():
                self._signal_name_to_alias[sig.port.name] = alname
                
        if signal_name in self._signal_name_to_alias:
            return self._signal_name_to_alias[signal_name]
        
        return signal_name
    
    def has_alias_for(self, signal_name:str):
        _alias = self.aliased_name_for(signal_name)
        return signal_name in self._signal_name_to_alias
        
                
    def __setattr__(self, name:str, value):
        if hasattr(self, '_added_signals') and name in self._added_signals \
            and isinstance(value, int):
            self._added_signals[name].value = value
            return 
        
        super().__setattr__(name, value)


