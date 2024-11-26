'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import asyncio
from microcotb.time.value import TimeValue
from microcotb.dut import DUT
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
            
_RunnerSingleton = None 
class Runner:
    
    @classmethod 
    def get(cls):
        global _RunnerSingleton
        if _RunnerSingleton is None:
            _RunnerSingleton = cls()
            
        return _RunnerSingleton
    
    @classmethod 
    def clear_all(cls):
        global _RunnerSingleton
        # clear the singleton 
        _RunnerSingleton = None
    
    def __init__(self):
        self.tests_to_run = dict()
        self.test_names = []
        
    def add_test(self, test:TestCase):
        if test.name is None:
            test.name = f'test_{test.function.__name__}'
        self.test_names.append(test.name)
        self.tests_to_run[test.name] = test
        
        
    def test(self, dut:DUT):
        from microcotb.time.system import SystemTime
        from microcotb.clock import Clock
        
        dut.testing_will_begin()
        
        num_failures = 0
        num_tests = len(self.test_names)
        #failures = dict()
        for test_count in range(num_tests):
            nm = self.test_names[test_count]
            SystemTime.reset()
            Clock.clear_all()
            test = self.tests_to_run[nm]
            
            if test.timeout is None:
                SystemTime.clear_timeout()
            else:
                SystemTime.set_timeout(test.timeout)
            
            
            test.failed = False
            try:
                dut._log.info(f"*** Running Test {test_count+1}/{num_tests}: {nm} ***") 
                test.run(dut)
                if test.expect_fail: 
                    num_failures += 1
                    dut._log.error(f"*** {nm} expected fail, so PASS ***")
                else:
                    dut._log.warn(f"*** Test '{nm}' PASS ***")
            except Exception as e:
                
                test.failed = True
                dut._log.error(exception_as_str(e))
                if len(e.args):
                    dut._log.error(f"T*** Test '{nm}' FAIL: {e.args[0]} ***")
                    if e.args[0] is None or not e.args[0]:
                        test.failed_msg = ''
                    else:
                        test.failed_msg = e.args[0]
                    
                num_failures += 1
            
                
        if num_failures:
            dut._log.warn(f"{num_failures}/{len(self.test_names)} tests failed")
        else:
            dut._log.info(f"All {len(self.test_names)} tests passed")
        
        dut._log.info("*** Summary ***")
        for nm in self.test_names:
            test = self.tests_to_run[nm]
            if test.failed:
                if test.expect_fail:
                    dut._log.warn(f"\tPASS\t{nm}\tFailed as expected {test.failed_msg}")
                else:
                    dut._log.error(f"\tFAIL\t{nm}\t{test.failed_msg}")
            else:
                if self.tests_to_run[nm].skip:
                    dut._log.warn(f"\tSKIP\t{nm}")
                else:
                    if test.expect_fail:
                        dut._log.error(f"\tFAIL\t{nm}\tpassed but expect_fail = True")
                    else:
                        dut._log.warn(f"\tPASS\t{nm}")
        
        
        

        

def test(func=None, *,
    timeout_time: float = None,
    timeout_unit: str = "step",
    expect_fail: bool = False,
    expect_error:Exception = None,
    skip: bool = False,
    stage: int = 0,
    name: str = None):
    
    def my_decorator_func(func):
        runner = Runner.get() 
        test_name = func.__name__ if name is None else name
        test_case = TestCase(test_name, func, 
                                timeout_time,
                                timeout_unit,
                                expect_fail,
                                expect_error,
                                skip,
                                stage)
        
        def wrapper_func(dut):  
            test_case.run(dut)
            
        runner.add_test(test_case)
        return wrapper_func
    
    return my_decorator_func
