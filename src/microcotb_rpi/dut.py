'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import microcotb.utils.tm as time
from .io import RPiIO
from microcotb.time.value import TimeValue
from microcotb.time.system import SystemTime


from microcotb.monitorable.io import MonitorableIO
from microcotb.monitorable.dut import MonitorableDUT, StateChangeReport


from microcotb.types.ioport import set_range_direction_python, \
    set_range_direction_verilog, range_direction_is_verilog

import microcotb.log as logging

log = logging.getLogger(__name__)
class Direction:
    INPUT = 0
    OUTPUT = 1
    CONFIGURABLE = 2
    

class DUT(MonitorableDUT):
    def __init__(self, name:str='PiDUT', 
                 state_change_callback=None,
                 configurable_port_suffix:str='_oe'):
        super().__init__(name, state_change_callback)
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
        for io in self.available_io(types_of_interest=(MonitorableIO,)):
            io.write_notifications_to = w_cb
            io.read_notifications_to = r_cb
            if io.name in seen:
                continue 
            
            seen[io.name] = True
            if isinstance(io, RPiIO) and io.has_inputs:
                self._port_with_inputs.append(io)
                    
    def poll_for_input_events(self, skip_io:MonitorableIO=None):
        
        for iowithinput in self._port_with_inputs:
            if (skip_io is None or skip_io != iowithinput):
                evts =  iowithinput.has_events()
                if not evts:
                    continue 
                #v = iowithinput.last_value
                self._report_and_cache(iowithinput, iowithinput.value) # force a read

                    
        
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
        self.poll_for_input_events(io)
    def _convert_to_list(self, val, valid_types, error_msg:str):
        
        if isinstance(val, valid_types):
            val = [val] # make a list 
        elif not isinstance(val, list):
            try:
                iterit = iter(val)
                val = list(iterit)
            except TypeError:
                raise TypeError(error_msg)
            
        return val
            
            
    def add_rpio(self, name:str, direction:int, 
                 pin_list:list, 
                 name_list:list=None, 
                 initial_value:int = None,
                 iochipname:str="/dev/gpiochip0"):
        '''
            add an I/O port using the GPIO lines.
            @param name: the name that will be available as obj.name 
            @param pin_list: list of pins in BIG endian [MSB ... LSB], like datasheets and verilog
            @param name_list: optional list of names to alias each pin
            @param iochipname: get the lines from here (default is /dev/gpiochip0) 
        '''
        log.info(f'Adding rpio {name}')
        pin_list = self._convert_to_list(pin_list, (int,), 'pin_list must be a list of pins')
        if name_list is not None:
            name_list = self._convert_to_list(pin_list, (str,), 'name_list must be a list of names')
            
            if len(pin_list) != len(name_list):
                log.warning("name list size mismatch")
            
        
        if range_direction_is_verilog():
            pin_list = list(reversed(pin_list))
            if name_list is not None:
                name_list = list(reversed(name_list))
            
        if hasattr(self, name):
            raise RuntimeError(f'Already have something called "{name}" in here')
        
        io = RPiIO(name, pin_list, iochipname)
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
        
        if initial_value is not None:
            log.info(f"Setting init value of {name} to {initial_value}")
            io.value = initial_value
            
        self.poll_for_input_events()
        if name_list is not None:
            for i in range(len(name_list)):
                if i >= len(pin_list):
                    log.warning(f'We have more names than pins here\n\t{pin_list}\n\t{name_list}')
                    return
            
            log.info(f'Adding alias {name_list[i]} for {name}[{i}]')
            self.add_bit_attribute(name_list[i], io, i)
                
            
            
    def __repr__(self):
        availNames = []
        for io in self.available_io():
            availNames.append(io.name)
        if not len(availNames):
            return f'<DUT {self.name}>'
        return f'<DUT {self.name} ({",".join(availNames)})>'
    
            