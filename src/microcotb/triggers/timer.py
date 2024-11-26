'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.triggers.awaitable import Awaitable
from microcotb.clock import Clock
from microcotb.time.value import TimeValue
from microcotb.time.system import SystemTime
class Timer(Awaitable):
    DebugTraceLoopCount = 1000
    def __init__(self, time:int, units:str):
        super().__init__()
        self.time = TimeValue(time, units)
        
    
    def run_timer(self):
        all_clocks = Clock.all()
        # print(f"All clocks on timer: {all_clocks}")
        if not all_clocks or not len(all_clocks):
            SystemTime.advance(self.time)
            return 
    
        fastest_clock = all_clocks[0]
        time_increment = fastest_clock.half_period
        target_time = SystemTime.current() + self.time
        increment_count = 0
        while SystemTime.current() < target_time:
            if self.DebugTraceLoopCount and increment_count % self.DebugTraceLoopCount == 0:
                print(f"Systime: {SystemTime.current()} (target {target_time})")
            
            increment_count += 1
            SystemTime.advance(time_increment)


                
    def __iter__(self):
        return self
    
    def __next__(self): 
        self.run_timer()
        raise StopIteration
    
    
    def __await__(self):
        self.run_timer()
        yield
        return self
    