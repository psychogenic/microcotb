'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import time
from .io import RPiIO, DebounceUSecs
from microcotb.time.value import TimeValue
from microcotb.time.system import SystemTime


from microcotb.monitorable.io import MonitorableIO
from microcotb.monitorable.dut import MonitorableDUT, StateChangeReport


from microcotb.types.ioport import set_range_direction_python, \
    set_range_direction_verilog, range_direction_is_verilog

class Direction:
    INPUT = 0
    OUTPUT = 1
    CONFIGURABLE = 2
    

class DUT(MonitorableDUT):
    def __init__(self, name:str='PiDUT', configurable_port_suffix:str='_oe'):
        super().__init__(name)
        self.configurable_port_suffix = configurable_port_suffix
        self._port_with_inputs = []

    @property 
    def is_monitoring(self):
        return self._is_monitoring
    
    @is_monitoring.setter
    def is_monitoring(self, set_to:bool):
        self._is_monitoring = True if set_to else False
        self.changed_monitoring()
            
        r_cb = self._io_val_read_cb if self._is_monitoring else None
        w_cb = self._io_val_written_cb if self._is_monitoring else None
        self._port_with_inputs = []
        seen = dict()
        for io in self.available_io():
            if isinstance(io, MonitorableIO):
                io.write_notifications_to = w_cb
                io.read_notifications_to = r_cb
                if io.name in seen:
                    continue 
                
                # print(f"XXXXX {io.name} {io.has_inputs}")
                seen[io.name] = True
                if isinstance(io, RPiIO) and io.has_inputs:
                    # print(f"{io.name} HAS INPUTS!!!!!!!!!!")
                    self._port_with_inputs.append(io)
                    
                    
        
    def _report_and_cache(self, io:MonitorableIO, value):
        if not self.is_monitoring:
            return 
        if not self.state_cache.has(io.port.name) or \
            self.state_cache.get(io.port.name) != value:
            stch = StateChangeReport()
            self.append_state_change(stch.add_change(io.port.name, value))
            self.state_cache.set(io.port.name, value)
            
        
    def _io_val_read_cb(self, io:MonitorableIO, val_read):
        self._report_and_cache(io, val_read)
    def _io_val_written_cb(self, io:MonitorableIO, value_written):
        if not self.is_monitoring:
            return 
        self._report_and_cache(io, value_written)
        
        time.sleep(0.001)
        for iowithinput in self._port_with_inputs:
            # print(f'check {iowithinput.name}')
            tm = 0.01 if iowithinput.name == 'uo_out' else 0.0002
            if io != iowithinput and iowithinput.has_events(tm):
                v = iowithinput.value
                # print(f'{iowithinput.name} EVENTS {bin(v)}')
                self._report_and_cache(iowithinput, v) # force a read
        
    def add_rpio(self, name:str, direction:int, pin_list:list, iochipname:str="/dev/gpiochip0"):
        
        if isinstance(pin_list, int):
            pin_list = [pin_list] # make a list 
        elif not isinstance(pin_list, list):
            try:
                iterit = iter(pin_list)
                pin_list = list(iterit)
            except TypeError:
                raise TypeError('pin_list must be a list or an int')
            
            
        
        if range_direction_is_verilog():
            pin_list = list(reversed(pin_list))
            
        io = RPiIO(name, pin_list, iochipname)
        if hasattr(self, name):
            raise RuntimeError(f'Already have something called "{name}" in here')
        setattr(self, name, io)
        if direction == Direction.INPUT:
            io.oe.value = 0
        elif direction == Direction.OUTPUT:
            
            io.oe.value = io.max_value
        elif direction == Direction.CONFIGURABLE:
            if not len(self.configurable_port_suffix):
                raise RuntimeError('Really need a prefix for configurable ports')
            pname = f"{name}{self.configurable_port_suffix}"
            if hasattr(self, pname):
                raise RuntimeError(f'Already have something called "{pname}" in here')
            
            setattr(self, pname, io.oe)
            
            
            