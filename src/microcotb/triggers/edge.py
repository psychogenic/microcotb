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
    DebugTraceLoopCount = 2000
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self._fastest_clock = None 
        self.initial_state = None
        self.primed = False
        self._cond_check_count = 0
        
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
            self._cond_check_count += 1
            if self.DebugTraceLoopCount is not None and \
                self._cond_check_count % self.DebugTraceLoopCount == 0:
                self.logger.info(f"SystemTime {SystemTime.current()}")
            SystemTime.advance(self.time_increment)
            
            
        if self.DebugTraceLoopCount is not None:
            self.logger.info(f"Done at {SystemTime.current()}")
        return
    
    
    def __iter__(self):
        self._cond_check_count = 0
        self._fastest_clock = None 
        self.prepare_for_wait()
        return self
    
    def __next__(self):
        self._cond_check_count = 0
        self.wait_for_conditions()
        raise StopIteration
    
    
    def __await__(self):
        self._cond_check_count = 0
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
            sval = self.signal_value
            if sval:
                # print(f"SIG VAL TRUE {sval}")
                return True
        else:
            if self.signal_value == 0:
                # print("PRIMED")
                self.primed = True 
            
            
    
    def __str__(self):
        return f'RisingEdge'

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
            
            
    def __str__(self):
        return f'FallingEdge'
        
        
        
        
        
        
        