'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.time.value import TimeValue
from microcotb.clock import Clock
import microcotb.utils.tm as time 

class SystemTimeout(Exception):
    pass

class SystemTime:
    _global_time = TimeValue(0, 'ns')
    _min_sleep_time = TimeValue(10, 'us')
    _timeout_setting = None
    
    @classmethod 
    def reset(cls):
        cls._global_time = TimeValue(0, 'ns')
        
    @classmethod 
    def current(cls) -> TimeValue:
        return cls._global_time
    
    @classmethod 
    def set_timeout(cls, delta_time:TimeValue):
        cls._timeout_setting = cls.current() + delta_time
        
    @classmethod 
    def clear_timeout(cls):
        cls._timeout_setting = None
        
        
    @classmethod 
    def set_units(cls, units:str):
        cls._global_time = TimeValue(cls._global_time.time, units)
        
    @classmethod 
    def advance(cls, time_or_timevalue, units:str=None):
        if isinstance(time_or_timevalue, TimeValue):
            tstep = time_or_timevalue
        elif isinstance(time_or_timevalue, int) and units is not None:
            tstep = TimeValue(time_or_timevalue, units)
        else:
            raise ValueError
        
        if cls._timeout_setting is not None:
            if cls._global_time > cls._timeout_setting:
                raise SystemTimeout(f'Timeout at {cls.current()}')
        
        cls._global_time += tstep
        if cls._min_sleep_time < tstep:
            time.sleep_us(int(tstep.time_in('us')))
                
        
        for clk in Clock.all():
            clk.time_is_now(cls._global_time)
            