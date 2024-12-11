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

from microcotb.monitorable.io import MonitorableIO
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
                 name:str='MONDUT',
                 state_change_callback=None):
        super().__init__(name)
        
        self.state_change_callback = state_change_callback
        
        self._write_test_vcds_to_dir = None
        self._write_vcd_enable = False
        self._is_monitoring = False
        self._queued_state_changes = []
        self.events_of_interest_per_test = dict()
        self._last_state_cache = StateCache()
        self._sub_fields = dict()
        self._watch_for_callbacks = dict()
        self._watch_for_handler = None
    
    
    # might wish to override (probably)
    def vcd_initial_state_reports(self):
        # override 
        # log.warning("No vcd_initial_state_reports -- override if needed")
        stch = StateChangeReport()
        for io in self.available_io():
            pass
            #FIXME if io.is_readable:
            #    stch.add_change(io.name, io.value)
                
        if len(stch):
            return [stch]
        return []
    
    
    # might wish to override (probably)
    @property 
    def is_monitoring(self):
        return self._is_monitoring
    
    @is_monitoring.setter
    def is_monitoring(self, set_to:bool):
        self._is_monitoring = True if set_to else False
        self.changed_monitoring()
    
    def _watch_for_triggered(self, stch:StateChangeReport):
        for name, cb in self._watch_for_callbacks.items():
            if stch.has(name):
                cb(name, stch.get(name), stch)
    
    def watch_for_state(self, io_name:str, callback):
        if callback is None: 
            # erasing
            if io_name in self._watch_for_callbacks:
                del self._watch_for_callbacks[io_name]
                if not len(self._watch_for_callbacks):
                    self._watch_for_handler = None 
                    
            return 
        self._watch_for_handler = self._watch_for_triggered
        self._watch_for_callbacks[io_name] = callback
        
    
    
    
    def changed_monitoring(self):
        if self._is_monitoring:
            SystemTime.ResetTime = TimeValue(1, TimeValue.BaseUnits)
        else:
            SystemTime.ResetTime = None
            self.state_cache.clear()
        
        
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
    
    def add_subfields_and_queue_state_change(self, atTime:TimeValue, report:StateChangeReport):
        self.add_subfields_to_report(report)
        self.queue_state_change(atTime, report)
        
    def queue_state_change(self, atTime:TimeValue, report:StateChangeReport):
        self._queued_state_changes.append(tuple([atTime, report]))
        
    def add_subfields_to_report(self, report:StateChangeReport):
        for name in report.changed():
            if name in self._sub_fields:
                #last_val = getattr(self, name).last_value_as_array
                #print(last_val)
                v = report.get(name)
                io = getattr(self, name)
                bin_str = io.port.value_as_array(v)
                
                for sf in self._sub_fields[name]:
                    cur_v = int(sf.out_of_array(bin_str))
                    if not self.state_cache.has(sf.name)\
                        or self.state_cache.get(sf.name) != cur_v:
                        self.state_cache.set(sf.name, cur_v)
                        report.add_change(sf.name, cur_v)
                    
    
    def append_state_change(self, stch:StateChangeReport):
        self.add_subfields_and_queue_state_change(SystemTime.current().clone(), stch)
        self.trigger_all_state_callbacks(stch)
        
    def trigger_all_state_callbacks(self, stch:StateChangeReport):
        if self.state_change_callback:
            cb = self.state_change_callback 
            cb(stch)
        if self._watch_for_handler:
            cb = self._watch_for_handler
            cb(stch)
            
    def store_queued_events_as_group(self, group_name:str):
        self.events_of_interest_per_test[group_name] = self.get_queued_state_changes()
        
    def testing_unit_start(self, test:microcotb.dut.TestCase):
        super().testing_unit_start(test)
        self.state_cache.clear()
        if self.write_vcd_enabled \
           and self.write_test_vcds_to_dir \
           and VCD.write_supported() :
            self._log.info("Test unit startup -- writing VCDs, get initial state")
            
            for report in self.vcd_initial_state_reports():
                self.add_subfields_and_queue_state_change(TimeValue(0, TimeValue.BaseUnits), report)
                
                
            
    
    def testing_unit_done(self, test:microcotb.dut.TestCase):
        if not self.write_vcd_enabled:
            self._log.info("No VCD writes enabled")
            return 
        if not self.write_test_vcds_to_dir:
            self._log.warning("Write VCD enabled, but NO vcds dir set?!")
            return 
        if test.skip:
            self._log.info("test skipped, no vcd write.")
            self.flush_queued_state_changes()
            return
        self.store_queued_events_as_group(test.name)
        fname = self.vcd_file_name(test)
        fpath = os.path.join(self.write_test_vcds_to_dir, f'{fname}.vcd')
        self._log.warning(f"writing VCD to '{fpath}'")
        try:
            self.write_vcd(test.name, fpath)
        except Exception as e:
            self._log.error(f"Issue writing VCD file {fpath}: {e}")
            
    def aliased_name_for(self, name:str):
        return name
         
    def get_queued_state_changes(self):
        v = self._queued_state_changes
        self.flush_queued_state_changes()
        return v
    def flush_queued_state_changes(self):
        self._queued_state_changes = []
        
    
    def dump_queued_events_as_vcd(self, name:str, indir:str=None):
        if not indir:
            if not self.write_test_vcds_to_dir:
                raise RuntimeError('Have not specified a write_test_vcds_to_dir or indir')
            indir = self.write_test_vcds_to_dir
        self.store_queued_events_as_group(name) 
        fpath = os.path.join(indir, f'{name}.vcd')
        self._log.warning(f"writing VCD to '{fpath}'")
        try:
            self.write_vcd(name, fpath)
        except Exception as e:
            self._log.error(f"Issue writing VCD file {fpath}: {e}")
        
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
            vcd.add_variable(varname, my_field.width, self.VCDScope)
            
        vcd.write_to(outputfile_path)
        
    
    def add_slice_attribute(self, name:str, source:MonitorableIO, idx_or_start:int, slice_end:int=None):
        rv = super().add_slice_attribute(name, source, idx_or_start, slice_end)
        if source.name not in self._sub_fields:
            self._sub_fields[source.name] = []
            
        self._sub_fields[source.name].append(rv)
        
        
    def add_bit_attribute(self, name:str, source:MonitorableIO, bit_idx:int):
        rv = super().add_bit_attribute(name, source, bit_idx)
        if source.name not in self._sub_fields:
            self._sub_fields[source.name] = []
        self._sub_fields[source.name].append(rv)
        return rv
