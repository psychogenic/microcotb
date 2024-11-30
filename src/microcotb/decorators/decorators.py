'''
Created on Nov 27, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from .parametrized import Parameterized
from microcotb.runner import Runner, TestCase

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
        if isinstance(func, Parameterized):
            for tf in func.generate_tests(
                                name=test_name,
                                timeout_time=timeout_time,
                                timeout_unit=timeout_unit,
                                expect_fail=expect_fail,
                                expect_error=expect_error,
                                skip=skip,
                                stage=stage
                                ):
                runner.add_test(tf)
            test_func = func.test_function
        else:
            test_case = TestCase(test_name, func, 
                                timeout_time,
                                timeout_unit,
                                expect_fail,
                                expect_error,
                                skip,
                                stage)
            
            
            runner.add_test(test_case)
            
            def wrapper_func(dut):  
                test_case.run(dut)
                
            test_func = wrapper_func
            
        return test_func
    
    return my_decorator_func