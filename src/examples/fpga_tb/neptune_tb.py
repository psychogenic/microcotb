'''
Created on Dec 7, 2024

All the tests themselves are in examples.common, this is just
specifics about how we're running

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import microcotb as cocotb
cocotb.set_runner_scope(__name__)

from examples.simple_usb_bridge.dut_sub import DUT, DefaultPort
import microcotb.log as logging
from microcotb.time.value import TimeValue

cocotb.set_runner_scope(__name__)

# get the @cocotb.test()s
import examples.common.neptune_tb

def main(dut:DUT = None):
    TimeValue.ReBaseStringUnits = True
    logging.basicConfig(level=logging.DEBUG)
    runner = cocotb.get_runner(__name__)
    if dut is None:
        dut = getDUT()
    dut._log.info(f"enabled neptune project, will test with {runner}")
    
    # enable saving VCDs
    dut.is_monitoring = False
    # dut.write_vcd_enabled = True
    dut.write_test_vcds_to_dir = '/tmp'
    
    runner.test(dut)


def getDUT(serial_port:str=DefaultPort, name:str='Neptune'):
    dut = DUT(serial_port, name, auto_discover=True)
    return dut

if __name__ == '__main__':
    main()
