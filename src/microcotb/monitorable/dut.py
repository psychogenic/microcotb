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
import os 
import re
from microcotb.ports.io import IO

import microcotb.dut 
from microcotb.time.value import TimeValue
from microcotb.time.system import SystemTime

from microcotb.monitorable.vcd_writer import Event, VCD
from microcotb.runner import TestCase
from microcotb.monitorable.state_tracking import StateChangeReport, StateCache


class MonitorableDUT(microcotb.dut.DUT):
    '''
        A DUT base class that allows for auto-discovery, tracking state changes
        (for VCD) and writing VCD output for tests, aliasing signals, etc.
    '''
    VCDScope = 'dut'
    def __init__(self, 
                 name:str='MONDUT'):
        super().__init__(name)
        self._write_test_vcds_to_dir = None
        self._write_vcd_enable = False
        self._is_monitoring = False
        self._queued_state_changes = []
        self.events_of_interest_per_test = dict()
        self._last_state_cache = StateCache()
    
    
    # might wish to override (probably)
    def vcd_initial_state_reports(self):
        # override 
        # log.warning("No vcd_initial_state_reports -- override if needed")
        return []
    
    
    # might wish to override (probably)
    @property 
    def is_monitoring(self):
        return self._is_monitoring
    
    @is_monitoring.setter
    def is_monitoring(self, set_to:bool):
        self._is_monitoring = True if set_to else False
        
    @property 
    def state_cache(self) -> StateCache:
        return self._last_state_cache
    
    
        
    @property
    def write_vcd_enabled(self):
        return self._write_vcd_enable 
    
    @write_vcd_enabled.setter
    def write_vcd_enabled(self, set_to:bool):
        self._write_vcd_enable = True if set_to else False # make it a bool 
        
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
    
    
    def testing_will_begin(self):
        super().testing_will_begin()
        if self.write_vcd_enabled:
            self._log.warning("VCD writes enabled")
            if not VCD.write_supported():
                self._log.warning("No VCD write support on platform")
                return 
            
            if self.is_monitoring:
                # so we can capture initial state without overwriting it
                SystemTime.ResetTime = TimeValue(1, TimeValue.BaseUnits)
            else:
                self._log.warning(f"Request to write VCDs to '{self.write_test_vcds_to_dir}'--but NO monitoring on.")
                
                
    @property 
    def queued_state_changes(self) -> list:
        return self._queued_state_changes    
    
    def queue_state_change(self, atTime:TimeValue, report:StateChangeReport):
        self._queued_state_changes.append(tuple([atTime, report]))
        
    def append_state_change(self, stch:StateChangeReport):
        self.queue_state_change(SystemTime.current().clone(), stch)
        
        
    def testing_unit_start(self, test:microcotb.dut.TestCase):
        super().testing_unit_start(test)
        self.state_cache.clear()
        if self.write_vcd_enabled \
           and self.write_test_vcds_to_dir \
           and VCD.write_supported() :
            self._log.info("Test unit startup -- writing VCDs, get initial state")
            
            for report in self.vcd_initial_state_reports():
                self.queue_state_change(TimeValue(0, TimeValue.BaseUnits), report)
                
                
            
    
    def testing_unit_done(self, test:microcotb.dut.TestCase):
        if not self.write_vcd_enabled:
            self._log.info("No VCD writes enabled")
            return 
        if not self.write_test_vcds_to_dir:
            self._log.warning("Write VCD enabled, but NO vcds dir set?!")
            return 
        self.events_of_interest_per_test[test.name] = self.get_queued_state_changes()
        fname = self.vcd_file_name(test)
        fpath = os.path.join(self.write_test_vcds_to_dir, f'{fname}.vcd')
        self._log.warning(f"writing VCD to '{fpath}'")
        try:
            self.write_vcd(test.name, fpath)
        except Exception as e:
            self._log.error(f"Issue writing VCD file {fpath}: {e}")
            
            
         
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
        
    def vcd_file_name(self, test:TestCase):
        nm = test.name
        return re.sub(r'[^a-zA-Z0-9]+', '_', nm)
        
    def write_vcd(self, test_name:str, outputfile_path:str, timescale:str='1 ns'):
        event_list = self.get_events(test_name)
        
        vcd = VCD(event_list, timescale)
        
        for varname in Event.variables_with_events():
            my_field = getattr(self, varname)
            vcd.add_variable(varname, my_field.port.width, self.VCDScope)
            
        vcd.write_to(outputfile_path)
    
    
