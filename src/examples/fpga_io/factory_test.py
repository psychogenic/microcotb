'''
Created on Dec 7, 2024

All the tests themselves are in examples.common, this is just
specifics about how we're running

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import microcotb as cocotb

cocotb.set_runner_scope(__name__)

# get the @cocotb.test()s
import examples.common.factory_test

from microcotb.time.value import TimeValue
from examples.fpga_io.tt_dut import TinyTapeoutDUT

import microcotb.log as logging

 
def main(dut:TinyTapeoutDUT = None):
    TimeValue.ReBaseStringUnits = True
    logging.basicConfig(level=logging.DEBUG)
    runner = cocotb.get_runner(__name__)
    if dut is None:
        dut = TinyTapeoutDUT('/dev/ttyACM0', 'FactoryTest', auto_discover=True)
    dut._log.info(f"enabled neptune project, will test with {runner}")
    
    # dut.is_monitoring = True
    # dut.write_test_vcds_to_dir = '/tmp'
    
    dut.uio_oe.value = 0 # all bidirs as inputs to start
    runner.test(dut)
    return dut

def getDUT(port:str='/dev/ttyACM0', start_readonly:bool=False):
    dut = TinyTapeoutDUT(port, 'TT', auto_discover=True, start_readonly=start_readonly)
    return dut



if __name__ == '__main__':
    main()