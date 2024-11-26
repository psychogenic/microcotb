'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.triggers.awaitable import Awaitable
from microcotb.clock import Clock
from microcotb.time.value import TimeValue
from microcotb.time.system import SystemTime

class Edge(Awaitable):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self._fastest_clock = None 
        self.initial_state = None
        self.primed = False
        
        
    @property 
    def signal_value(self):
        return int(self.signal.value)
    
    def prepare_for_wait(self):
        return 
    def conditions_met(self):
        print("OVERRIDE ME")
        return False
    
    @property 
    def fastest_clock(self) -> Clock:
        if self._fastest_clock is None:
            self._fastest_clock = Clock.get_fastest()
            
        return self._fastest_clock
    
    @property 
    def time_increment(self) -> TimeValue:
        return self.fastest_clock.half_period
    
    def wait_for_conditions(self):
        while not self.conditions_met():
            SystemTime.advance(self.time_increment)
            
        return
    
    
    def __iter__(self):
        self._fastest_clock = None 
        self.prepare_for_wait()
        return self
    
    def __next__(self):
        self.wait_for_conditions()
        raise StopIteration
    
    
    def __await__(self):
        self._fastest_clock = None 
        self.prepare_for_wait()
        self.wait_for_conditions()
        yield
        return self
    

class RisingEdge(Edge):
    def __init__(self, signal):
        super().__init__(signal)
            
    def prepare_for_wait(self):
        self.initial_state = self.signal_value
        self.primed = False if self.initial_state else True
        # print(f"Initial state: {self.initial_state} and primed {self.primed}")
        return 
    
    def conditions_met(self):
        if self.primed:
            if self.signal_value:
                return True
        else:
            if self.signal_value == 0:
                self.primed = True 
            
            
        

class FallingEdge(Edge):
    def __init__(self, signal):
        super().__init__(signal)
            
    def prepare_for_wait(self):
        self.initial_state = self.signal_value
        self.primed = True if self.initial_state else False
        return 
    
    def conditions_met(self):
        if self.primed:
            if self.signal_value == 0:
                return True
        else:
            if self.signal_value:
                self.primed = True
            
            
        
        
        
        
        
        
        