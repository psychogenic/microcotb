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
from microcotb.time.value import TimeValue
from microcotb.time.system import SystemTime

from examples.simple_usb_bridge.signal import Signal
from examples.simple_usb_bridge.vcd_writer import Event, VCD

log = logging.getLogger(__name__)


class StateChangeReport:
    '''
        Base interface for a State Change Report.
    '''
    def __init__(self):
        self._changed_ports = dict()
        self._num_changes = 0
    def add_change(self, pname:str, pvalue:int):
        self._changed_ports[pname] = pvalue
        setattr(self, pname, pvalue)
        self._num_changes += 1
    def changed(self):
        return list(self._changed_ports.keys())     
    def all_changes(self):
        return list(self._changed_ports.items())
    def __len__(self):
        return len(self._changed_ports)
    def __repr__(self):
        return f'<StateChangeReport with {len(self._changed_ports)} (in {self._num_changes}) changes>'
    
    def __str__(self):
        outlist = []
        for k,v in self._changed_ports.items():
            outlist.append(f'{k} = {hex(v)}')
        if not len(outlist):
            return 'StateChangeReport: no changes'
        sep = '\n'
        return f"StateChangeReport ({len(outlist)} ports in {self._num_changes} events):\n{sep.join(outlist)}"
            
  

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

class DUT(microcotb.dut.DUT):
    '''
        A DUT base class that allows for auto-discovery, tracking state changes
        (for VCD) and writing VCD output for tests, aliasing signals, etc.
    '''
    def __init__(self, 
                 name:str='SUB', 
                 auto_discover:bool=False):
        super().__init__(name)
        self._write_test_vcds_to_dir = None
        self._added_signals = dict()
        self._signal_by_address = dict()
        self._alias_to_signal = dict()
        self._is_monitoring = False
        self._queued_state_changes = []
        self._signal_name_to_alias = None
        self.events_of_interest_per_test = dict()
        
        if auto_discover:
            self.discover()
            
    @property 
    def write_test_vcds_to_dir(self):
        return self._write_test_vcds_to_dir
    
    @write_test_vcds_to_dir.setter 
    def write_test_vcds_to_dir(self, set_to:str):
        if not VCD.write_supported():
            raise RuntimeError('no VCD write support on platform')
        
        if set_to is not None and not os.path.exists(set_to):
            raise ValueError(f'VCD write path "{set_to}" DNE')
        
        self._write_test_vcds_to_dir = set_to
            
    def add_signal(self, name, addr, width:int, is_writeable_input:bool=False):
        log.error("Override add_signal")
        raise RuntimeError('add_signal needs override')
        return 
    
    def discover(self):
        log.error('override discover')
        raise RuntimeError('discover needs override')
        return
    
    
    
    def testing_will_begin(self):
        # use auto-discover instead self.discover()
        super().testing_will_begin()
        if self.write_test_vcds_to_dir:
            if not VCD.write_supported():
                log.warn("No VCD write support on platform")
                return 
            if not self.is_monitoring:
                log.warn(f"Request to write VCDs to '{self.write_test_vcds_to_dir}'--activating monitoring")
                self.is_monitoring = True
                # so we can capture initial state
                SystemTime.ResetTime = TimeValue(1, TimeValue.BaseUnits)
                
    def testing_unit_start(self, test:microcotb.dut.TestCase):
        if self.write_test_vcds_to_dir and VCD.write_supported() and self.is_monitoring:
            log.info("Test unit startup -- writing VCDs, get initial state")
            stateChange = StateChangeReport()
            for signame in self._added_signals.keys():
                if self.has_alias_for(signame):
                    continue #skip aliase
                s = self._added_signals[signame]
                log.debug(f"Initial state {signame} = {s.value}")
                stateChange.add_change(signame, s.value)
            if len(stateChange):
                self._queued_state_changes.append(tuple([TimeValue(0, TimeValue.BaseUnits), stateChange]))
                
                
            
    
    def testing_unit_done(self, test:microcotb.dut.TestCase):
        for s in self._added_signals.values():
            s.reset()
            
        if self.is_monitoring:
            self.events_of_interest_per_test[test.name] = self.get_queued_state_changes()
            if self.write_test_vcds_to_dir:
                fpath = os.path.join(self.write_test_vcds_to_dir, f'{test.name}.vcd')
                log.warn(f"writing VCD to '{fpath}'")
                try:
                    self.write_vcd(test.name, fpath)
                except:
                    log.error(f"Issue writing VCD file {fpath}")
            
            
         
    
    def _append_state_change(self, stch:StateChangeReport):
        self._queued_state_changes.append(tuple([SystemTime.current().clone(), stch]))
        
    def get_queued_state_changes(self):
        v = self._queued_state_changes
        self._queued_state_changes = []
        return v
    
    def dump_queued_state_changes(self):
        v = self.get_queued_state_changes()
        for st in v:
            print(st[1])
    
    def get_events(self, test_name:str):
        if test_name not in self.events_of_interest_per_test:
            print(f'No "{test_name}" events found')
            
            print(f'Available: {",".join(self.events_of_interest_per_test.keys())}')
            return 
        event_list = []
        Event.reset_known_variables()
        for ev in self.events_of_interest_per_test[test_name]:
            ev_time = ev[0]
            # print(f'{ev[0]}: ', end='')
            #changes = []
            for changed_field in ev[1].changed():
                s_name = self.aliased_name_for(changed_field)
                ev_val = getattr(ev[1], changed_field)
                event_list.append(Event(ev_time, s_name, ev_val))
                #changes.append(f'{s_name} = {hex(getattr(ev[1], changed_field))}')
                
            #print(','.join(changes))
        return event_list
        
    def write_vcd(self, test_name:str, outputfile_path:str, timescale:str='1 ns'):
        event_list = self.get_events(test_name)
        
        vcd = VCD(event_list, timescale)
        
        for varname in Event.variables_with_events():
            my_field = getattr(self, varname)
            vcd.add_variable(varname, my_field.port.width, 'dut')
            
        vcd.write_to(outputfile_path)
    
    

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
        
        
        
    @property 
    def is_monitoring(self):
        return self._is_monitoring
    
    @is_monitoring.setter
    def is_monitoring(self, set_to:bool):
        self._is_monitoring = True if set_to else False
        

        
                
    def __setattr__(self, name:str, value):
        if hasattr(self, '_added_signals') and name in self._added_signals \
            and isinstance(value, int):
            self._added_signals[name].value = value
            return 
        
        super().__setattr__(name, value)


