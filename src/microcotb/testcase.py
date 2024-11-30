'''
Created on Nov 27, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import asyncio
from microcotb.time.value import TimeValue
from microcotb.platform import exception_as_str

class TestCase:
    def __init__(self, 
                name:str, 
                func,
                timeout_time: float = None,
                timeout_unit: str = '',
                expect_fail: bool = False,
                expect_error:Exception = None,
                skip: bool = False,
                stage: int = 0):
        self.name = name 
        self.function = func
        self.timeout = None
        if timeout_time is not None:
            if not len(timeout_unit):
                raise ValueError('Must specify a timeout_unit when using timeouts')
            self.timeout = TimeValue(timeout_time, timeout_unit)
        
        self.expect_fail = expect_fail
        self.expect_error = expect_error
        self.skip = skip
        self.stage = stage
        self.failed = False
        self.failed_msg = ''
        self._run_time = None
        self.real_time = 0
        
    def run(self, dut):
        if self.skip:
            dut._log.warn(f"{self.name} skip=True")
            return 
        func = self.function
        try:
            asyncio.run(func(dut))
        except Exception as e:
            self.failed = True
            if not self.expect_fail:
                raise e
            dut._log.error(exception_as_str(e))
            dut._log.warn("Failure was expected")
    @property 
    def run_time(self) -> TimeValue:
        return self._run_time
    
    @run_time.setter 
    def run_time(self, t:TimeValue):
        self._run_time = TimeValue(t.time, t.units)
        
    
    def __repr__(self):
        rstr = f'<TestCase {self.name}'
        if self.skip:
            rstr += ' skip=True' 
            
        if self.expect_fail:
            rstr += ' fail=True'
            
        if self.timeout is not None:
            rstr += f' timeout={self.timeout.time}{self.timeout.units}'
        
        return rstr + '>'
        