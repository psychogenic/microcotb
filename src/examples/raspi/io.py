'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.monitorable.io import IO, MonitorableIO
import gpiod
from gpiod.line import Direction, Value, Edge
import datetime 
import time


DebounceUSecs = 500
ResilientReads = False

class ConfigurableDirectionIO(IO):
    
    def oe_value_change(self, oe:IO, current_value:int, new_value:int):
        pass

class RPiOE(IO):
    def __init__(self, name:str, width:int, managed_io:ConfigurableDirectionIO):
        super().__init__(f'{name}_oe', width, self.current_value, self.set_current_value)
        self._managed_name = name
        self._current_value = 0
        self._managed_io = managed_io
        self._write_notif_callback = None 
        
    def managed_port_name(self):
        return self._managed_name
        
    def current_value(self) -> int:
        return self._current_value
    
    def set_current_value(self, set_to:int):
        old_val = self._current_value
        self._current_value = set_to 
        self._managed_io.oe_value_change(self, old_val, set_to)
        
        

class RPiIO(MonitorableIO):
    def __init__(self, name:str, pin_list:list, chipname:str="/dev/gpiochip0"):
        width = len(pin_list)
        super().__init__(name, width, self._get_line_values, self._set_line_values)
        self.oe = RPiOE(name, width, self)
        self._chipname = chipname
        self._pin_ids = pin_list
        oe_value = self.oe.value
        self._config = dict()
        for i in range(width):
            self._config[self._pin_ids[i]] = self._get_line_settings_config(int(oe_value[i]))
            
        self._line_request = gpiod.request_lines(self._chipname, consumer='microcotb', 
                                                 config=self._config)
        
    
    @property
    def has_inputs(self):
        return self.oe.current_value() < self.oe.max_value
    
    def has_events(self, timeout=0.0001):
        if self._line_request.wait_edge_events(timeout):
            num = len(self._line_request.read_edge_events())
            # print(f'NUM EVENTS! {num}')
            return num 
        return None
    
    @property 
    def line_request(self) -> gpiod.LineRequest:
        return self._line_request
    
    def _get_line_settings_config(self, for_output:bool) -> gpiod.LineSettings:
        if for_output:
            return gpiod.LineSettings(
                            direction=Direction.OUTPUT, output_value=Value.ACTIVE
                        )
        
        return gpiod.LineSettings(
                            direction=Direction.INPUT, edge_detection=Edge.BOTH,
                            debounce_period=datetime.timedelta(microseconds=DebounceUSecs))
    def _get_line_resilient(self):
        attempt = 0
        vo = [1, 2]
        while vo[0] != vo[1]:
            if attempt:
                print(f'ATTEMPT {attempt} on {self.name}: {vo}')
            attempt += 1
            for a in range(2):
                
                v = 0
                cur_vals = self.line_request.get_values()
                for i in range(len(cur_vals)):
                    if cur_vals[i].value:
                        v |= (1 << i)
                vo[a] = v
                
                time.sleep(1.1*DebounceUSecs/1e6)
                
        return vo[0]
        
    def _get_line_values(self):
        # time.sleep(DebounceUSecs/1e6)
        if ResilientReads:
            return self._get_line_resilient()
        v = 0
        cur_vals = self.line_request.get_values()
        for i in range(len(cur_vals)):
            if cur_vals[i].value:
                v |= (1 << i)
        return v
    
    def _set_line_values(self, set_to:int):
        
        oe_value = self.oe.value
        set_val_conf = dict()
        for i in range(len(oe_value)):    
            if oe_value[i] == True:
                set_val_conf[self._pin_ids[i]] =  Value.ACTIVE if (set_to & (1 << i)) else Value.INACTIVE
        
        if len(set_val_conf):
            self.line_request.set_values(set_val_conf)
                
    @property 
    def pin_ids(self):
        return self._pin_ids
    
    def oe_value_change(self, oe:IO, current_value:int, new_value:int):
        changed = current_value ^ new_value
        if not changed:
            return
        new_config = dict()
        for i in range(self.port.width):
            if changed & (1 << i):
                new_settings = self._get_line_settings_config(new_value & (1 << i) )
                new_config[self._pin_ids[i]] = new_settings
            else:
                new_config[self._pin_ids[i]] = self._config[self._pin_ids[i]]
        
        self.line_request.reconfigure_lines(new_config)
        
                
                
