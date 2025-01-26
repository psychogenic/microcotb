'''
Created on Dec 8, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

OutputVCD = True 

 
import microcotb as cocotb

cocotb.set_runner_scope(__name__)

# get the @cocotb.test()s
import examples.common.factory_test

from microcotb.time.value import TimeValue
from examples.raspi.tt_dut import TinyTapeoutDUT

import microcotb.log as logging
from microcotb.time.system import SystemTime
 
def main(dut:TinyTapeoutDUT = None):
    TimeValue.ReBaseStringUnits = True
    logging.basicConfig(level=logging.INFO)
    
    runner = cocotb.get_runner(__name__)
    if dut is None:
        dut = TinyTapeoutDUT('FactoryTest')
    dut._log.info(f"will test with {runner}")
    if OutputVCD:
        dut.is_monitoring = True
        dut.write_vcd_enabled = True
        dut.write_test_vcds_to_dir = '/tmp'
    else:
        # need to slow things a bit
        SystemTime.ForceSleepOnAdvance = 0.005
    
    dut.uio_oe.value = 0 # all bidirs as inputs to start
    runner.test(dut)
    return dut

def getDUT():
    dut = TinyTapeoutDUT('TT')
    return dut



if __name__ == '__main__':
    main()