'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.testcase import TestCase
from microcotb.dut import DUT
from microcotb.platform import exception_as_str
import microcotb.utils.tm as time
    
_RunnerSingleton = None 
class Runner:
    SummaryNameFieldLen = 40
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
        all_tests_start_s = time.runtime_start()
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
                t_start_s = time.runtime_start()
                test.run(dut)
                if test.expect_fail: 
                    num_failures += 1
                    dut._log.error(f"*** {nm} expected fail, so PASS ***")
                else:
                    dut._log.warn(f"*** Test '{nm}' PASS ***")
            except KeyboardInterrupt:
                test.failed = True 
                test.failed_msg = 'Keyboard interrupt'
                num_failures += 1
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
                
            test.real_time = time.runtime_delta_secs(t_start_s)
            test.run_time = SystemTime.current()
            dut.testing_unit_done(test)
            
        all_tests_runs_time = time.runtime_delta_secs(all_tests_start_s)
        dut.testing_done()
        
        
        if num_failures:
            dut._log.warn(f"{num_failures}/{len(self.test_names)} tests failed")
        else:
            dut._log.info(f"All {len(self.test_names)} tests passed")
        
        dut._log.info("*** Summary ***")
        max_name_len = self.SummaryNameFieldLen
        dut._log.warn(f"\tresult\t{' '*max_name_len}\tsim time\treal time\terror")
        for nm in self.test_names:
            
            if len(nm) < max_name_len:
                spaces = ' '*(max_name_len - len(nm))
            else:
                spaces = ''
            test = self.tests_to_run[nm]
            realtime = f'{test.real_time:.4f}s'
            if test.failed:
                if test.expect_fail:
                    dut._log.warn(f"\tPASS\t{nm}{spaces}\t{test.run_time}\t{realtime}\tFailed as expected {test.failed_msg}")
                else:
                    dut._log.error(f"\tFAIL\t{nm}{spaces}\t{test.run_time}\t{realtime}\t{test.failed_msg}")
            else:
                if self.tests_to_run[nm].skip:
                    dut._log.warn(f"\tSKIP\t{nm}{spaces}\t--")
                else:
                    if test.expect_fail:
                        dut._log.error(f"\tFAIL\t{nm}{spaces}\t{test.run_time}\t{realtime}\tpassed but expect_fail = True")
                    else:
                        dut._log.warn(f"\tPASS\t{nm}{spaces}\t{test.run_time}\t{realtime}")
        dut._log.info(f"Real run time: {all_tests_runs_time:.4f}s")
        
    def __len__(self):
        return len(self.tests_to_run)
    def __repr__(self):
        return f'<Runner [{len(self)} Tests]>'
    
    def __str__(self):
        # get strings for each test, in order of appearance
        test_strs = list(map(lambda x: f"\t{x}", map(lambda nm: self.tests_to_run[nm], self.test_names)))
        return f'Runner with {len(self)} test cases:\n' + '\n'.join(test_strs)
        
        

