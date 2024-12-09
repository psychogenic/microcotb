'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.testcase import TestCase
from microcotb.dut import DUT
from microcotb.platform import exception_as_str
import microcotb.utils.tm as time
import microcotb.platform as plat
import microcotb.log as logging
_RunnerSingletonByName = None
PropExceptions = False # just for debug


class Runner:
    SummaryNameFieldLen = 40
    @classmethod 
    def get(cls, test_module:str):
        global _RunnerSingletonByName
        if _RunnerSingletonByName is None:
            _RunnerSingletonByName = dict() 
        
        if test_module not in _RunnerSingletonByName:   
            _RunnerSingletonByName[test_module] = cls()
            
        return _RunnerSingletonByName[test_module]
    
    
    
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
            if plat.Features.FunctionsHaveQualifiedNames:
                test.name = f'test_{test.function.__qualname__}'
            else:
                test.name = f'test_{test.function.__name__}'
        self.test_names.append(test.name)
        self.tests_to_run[test.name] = test
        
        
    def test(self, dut:DUT):
        from microcotb.time.system import SystemTime
        from microcotb.clock import Clock
        steps_p_sec_tot = 0
        num_stepps_avged = 0
        dut.testing_will_begin()
        all_tests_start_s = time.runtime_start()
        num_failures = 0
        num_tests = len(self.test_names)
        
        log = dut._log.getChild('x')
        log.name = 'runner'
        
        if not num_tests:
            log.error("No tests to run!")
            return 
        
        
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
                log.warning(f"*** Running Test {test_count+1}/{num_tests}: {nm} ***") 
                t_start_s = time.runtime_start()
                if not test.skip:
                    dut.testing_unit_start(test)
                    test.run(dut)
                    if test.expect_fail: 
                        num_failures += 1
                        log.error(f"*** {nm} expected fail, but PASSed***")
                    else:
                        log.warning(f"*** Test '{nm}' PASS ***")
            except KeyboardInterrupt:
                test.failed = True 
                test.failed_msg = f'Keyboard interrupt @ {SystemTime.current()}'
                num_failures += 1
            except Exception as e:
                test.failed = True
                log.error(exception_as_str(e))
                if len(e.args):
                    log.error(f"T*** Test '{nm}' FAIL: {e.args[0]} {e}***")
                    if e.args[0] is None or not e.args[0]:
                        test.failed_msg = ''
                    else:
                        test.failed_msg = e.args[0]
                num_failures += 1
                if PropExceptions:
                    raise e
                
            test.real_time = time.runtime_delta_secs(t_start_s)
            test.run_time = SystemTime.current()
            if test.skip: 
                log.info(f'{test.name} skipped')
                continue 
            
            shortest_interval = Clock.get_shortest_event_interval()
            if shortest_interval is None:
                log.warning('No clocks in test')
            else:
                if test.real_time:
                    steps_per_sec = (1/shortest_interval.time_in('sec'))/test.real_time
                    log.info(f'Ran @ {steps_per_sec:.2f} steps/s')
                    steps_p_sec_tot += steps_per_sec
                    num_stepps_avged += 1
                dut.testing_unit_done(test)
            
        all_tests_runs_time = time.runtime_delta_secs(all_tests_start_s)
        dut.testing_done()
        
        
        if num_failures:
            log.warning(f"{num_failures}/{len(self.test_names)} tests failed")
        else:
            log.info(f"All {len(self.test_names)} tests passed")
        
        log.info("*** Summary ***")
        max_name_len = self.SummaryNameFieldLen
        log.warning(f"\tresult\t{' '*max_name_len}\tsim time\treal time\terror")
        for nm in self.test_names:
            
            if len(nm) < max_name_len:
                spaces = ' '*(max_name_len - len(nm))
            else:
                spaces = ''
            test = self.tests_to_run[nm]
            realtime = f'{test.real_time:.4f}s'
            if test.failed:
                if test.expect_fail:
                    log.warning(f"\tPASS\t{nm}{spaces}\t{test.run_time}\t{realtime}\tFailed as expected {test.failed_msg}")
                else:
                    log.error(f"\tFAIL\t{nm}{spaces}\t{test.run_time}\t{realtime}\t{test.failed_msg}")
            else:
                if self.tests_to_run[nm].skip:
                    log.warning(f"\tSKIP\t{nm}{spaces}\t--")
                else:
                    if test.expect_fail:
                        log.error(f"\tFAIL\t{nm}{spaces}\t{test.run_time}\t{realtime}\tpassed but expect_fail = True")
                    else:
                        log.warning(f"\tPASS\t{nm}{spaces}\t{test.run_time}\t{realtime}")
        stpss_avg = 0
        if num_stepps_avged:
            stpss_avg =  steps_p_sec_tot / num_stepps_avged
        log.info(f"Real run time: {all_tests_runs_time:.4f}s ({stpss_avg:.2f} steps/s avg)")
        
    def __len__(self):
        return len(self.tests_to_run)
    def __repr__(self):
        return f'<Runner [{len(self)} Tests]>'
    
    def __str__(self):
        # get strings for each test, in order of appearance
        test_strs = list(map(lambda x: f"\t{x}", map(lambda nm: self.tests_to_run[nm], self.test_names)))
        return f'Runner with {len(self)} test cases:\n' + '\n'.join(test_strs)
        
        

