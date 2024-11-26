'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.triggers.awaitable import Awaitable
from microcotb.clock import Clock
from microcotb.time.system import SystemTime
    
class ClockCycles(Awaitable):
    def __init__(self, sig, num_cycles:int, rising:bool=True):
        super().__init__(sig)
        self.num_cycles = num_cycles
        self.num_transitions = 0
        self.rising = rising
        
    def __iter__(self):
        return self

    def next(self): 
        clk = Clock.get(self.signal)
        
        self.num_transitions = self.num_cycles * 2
        if (self.rising and self.signal.value == 0 or
            not self.rising and self.signal.value == 1):
            self.num_transitions -= 1
        
        if clk is None:
            print("CLK NO CLK")
        else:
            target_time = SystemTime.current() + (clk.half_period * self.num_transitions)
            time_increment = Clock.get_shortest_event_interval()
            #print(f"Is now {SystemTime.current()}, running until {target_time}, increment is {time_increment}")
            while SystemTime.current() < target_time:
                #print("Advancing time")
                SystemTime.advance(time_increment)
                
        raise StopIteration
    
    def __next__(self):
        return self.next()
    
    def __await__(self):
        clk = Clock.get(self.signal)
        if clk is not None:
            self.cycle_count = 0
            for _i in range(self.num_cycles):
                clk.tick()
        yield
        return self
    