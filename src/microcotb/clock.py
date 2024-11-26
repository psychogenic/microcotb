'''
Created on Nov 21, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import gc 
from microcotb.time import TimeValue
gc.collect()

_ClockForSignal = dict()     
class Clock:
    @classmethod 
    def get(cls, signal):
        global _ClockForSignal
        if signal in _ClockForSignal:
            return _ClockForSignal[signal]
        return None
    
    @classmethod 
    def get_fastest(cls):
        all_clocks = cls.all()
        if len(all_clocks) < 1:
            return None 
        return all_clocks[0]
    
    @classmethod 
    def get_shortest_event_interval(cls) -> TimeValue:
        fastest = cls.get_fastest()
        if fastest is not None:
            return fastest.half_period
        return None
    
    @classmethod
    def clear_all(cls):
        global _ClockForSignal
        _ClockForSignal = dict()
        
    @classmethod 
    def all(cls):
        global _ClockForSignal
        vals = list(_ClockForSignal.values())
        if len(vals) < 2:
            return vals
        
        return sorted(vals, key=lambda x: float(x.half_period))
    
    def __init__(self, signal, period, units):
        self.signal = signal
        self.running = False
        
        half_period = TimeValue(period/2, units)
        
        # we need next toggle to be just before half period
        # so we try and convert to smaller units, to keep precision 
        # and make everything directly comparable
        hp_smaller_units = half_period.cast_stepdown_units()
        if hp_smaller_units is not None:
            half_period = hp_smaller_units
            next_toggle = TimeValue(half_period.time - 5, half_period.units)
        else:
            if half_period.time > 1:
                next_toggle = TimeValue(half_period.time - 1, half_period.units)
            else:
                next_toggle = half_period
        
        self.half_period = half_period
        self.next_toggle = next_toggle
        
        self.current_signal_value = 0
        self.sleep_us = 0
        half_per_secs = float(self.half_period)
        if  half_per_secs > 200e-6:
            self.sleep_us = round(half_per_secs*1e6)
            
        self._toggle_count = 0
        self._period = None 
        
    @property 
    def period(self):
        if self._period is None:
            self._period = self.half_period * 2
        
        return self._period
    @property 
    def event_interval(self):
        return self.half_period
    
    def start(self):
        global _ClockForSignal
        _ClockForSignal[self.signal] = self
        
    def num_events_in(self, time_or_timevalue:int, units:str=None):
        if isinstance(time_or_timevalue, TimeValue):
            tv = time_or_timevalue 
        elif units is not None:
            tv = TimeValue(time_or_timevalue, units)
        else:
            raise ValueError
        return tv / self.half_period
    
    def time_is_now(self, currentTime:TimeValue):
        while self.next_toggle < currentTime:
            self.toggle()
            self.next_toggle += self.half_period
        
    def time_has_passed(self):
        #print(f"time passed to {SystemTime.current()} next is {self.next_toggle}")
        from microcotb.time.system import SystemTime
        self.time_is_now(SystemTime.current())
    
    def toggle(self):
        new_val = 1 if not self.current_signal_value else 0
        self.signal.value = new_val 
        self.current_signal_value = new_val
    
    def tick(self):
        # clock will go through whole period, end where it started
        self.toggle()
        self.toggle()
        
    def __repr__(self):
        return f'<Clock {self.period} on {self.signal}>'
        
    