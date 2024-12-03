'''
Created on Dec 2, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.clock import Clock
from microcotb.triggers import ClockCycles 
import microcotb as cocotb
import microcotb.log as logging
from microcotb.time.value import TimeValue
from microcotb.triggers.edge import RisingEdge

from examples.simple_usb_bridge.dut_sub import DUT, DefaultPort

async def ack_register_rcvd(dut):
    
    dut._log.info("ACK reg processed")
    await ClockCycles(dut.clk, 5)
    
    dut.register_processed.value = 1
    await ClockCycles(dut.clk, 1)
    dut.register_processed.value = 0
    await ClockCycles(dut.clk, 1)
    
    
@cocotb.test(timeout_time=300, timeout_unit='ms')
async def test_parse(dut):
    
    num_samples = 35 # number of registers to fetch
    
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # startup disabled
    dut.start_address.value = 0 # beginning of flash
    dut.enable.value = 0
    await ClockCycles(dut.clk, 10)
    
    # enable
    dut.enable.value = 1
    await ClockCycles(dut.clk, 2)
    # we should startup without a valid value
    assert dut.value_valid.value == 0, "Valid value already asserted"
    
    # now it'll read in the file header
    dut._log.info("Waiting on value_valid, first one takes a while...")
    await RisingEdge(dut.value_valid)
    dut._log.info(f"Got it, clocking in {num_samples}")
    
    
    count_valids = 0
    while count_valids < num_samples:
        
        if dut.fresh_sample.value == 1:
            while not int(dut.value_valid.value):
                await ClockCycles(dut.clk, 2)
            
            dut._log.info("Got fresh reg set!!")
            await ack_register_rcvd(dut)
        
        if not int(dut.value_valid.value):
            await RisingEdge(dut.value_valid)
            dut._log.debug(f"GOT RISING EDGE ON value_valid")
        
        count_valids += 1
        dut._log.info(f"Got valid reg, now have got {count_valids}")
        await ack_register_rcvd(dut)
        

def main(dut:DUT = None):
    TimeValue.ReBaseStringUnits = True
    logging.basicConfig(level=logging.DEBUG)
    runner = cocotb.get_runner()
    if dut is None:
        dut = getDUT()
    dut._log.info(f"enabled SPI Parser (PSYM Reader) project, will test with {runner}")
    
    # get state changes asynchronously:
    dut.is_monitoring = True
    # write a VCD for every test run
    dut.write_test_vcds_to_dir = '/tmp'
    
    # run them tests
    runner.test(dut)


def getDUT(serial_port:str=DefaultPort, name:str='PSYMRDR'):
    dut = DUT(serial_port, name, auto_discover=True)
    return dut

if __name__ == '__main__':
    main()
