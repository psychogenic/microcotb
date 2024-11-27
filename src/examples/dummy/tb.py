'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

import microcotb as cocotb

from microcotb.clock import Clock
from microcotb.triggers import ClockCycles, Timer, RisingEdge, FallingEdge
from microcotb.utils import get_sim_time

async def reset(dut):
    # Reset
    dut._log.info("Reset")
    dut.rst_n.value = 0
    dut.count_en.value = 0
    dut.input.value = 0
    await ClockCycles(dut.clk, 1)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)
    
@cocotb.test()
async def test_loopback(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    await reset(dut)

    for i in range(256):
        dut.input.value = i
        await ClockCycles(dut.clk, 1)
        assert dut.output.value == i, f"no loop? {dut.output.value} != {i}"

    dut._log.info("test_loopback passed")


@cocotb.test()
async def test_counter(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    start_count = 5
    
    await reset(dut)
    
    dut.input.value = start_count
    await ClockCycles(dut.clk, 1)
    
    assert dut.output.value == start_count, f"output should be {start_count}"
    
    dut.count_en.value = 1

    for i in range(100):
        assert dut.output.value == (i + start_count), f"no counting? {dut.output.value} != {i + start_count}"
        await ClockCycles(dut.clk, 1)

    dut._log.info("test_counter passed")


@cocotb.test()
async def test_edge_triggers(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    await reset(dut)
    
    dut.count_en.value = 1

    dut._log.info(f"Testing counter, waiting on rising edge of bit 5 at {get_sim_time('us')}us")
    await RisingEdge(dut.some_bit)
    dut._log.info(f"Got rising edge, now {get_sim_time('us')}us value is {hex(dut.output.value)}")
    
    dut._log.info(f"Now await falling edge")
    await FallingEdge(dut.some_bit)
    dut._log.info(f"Got rising edge, now {get_sim_time('us')}us value is {hex(dut.output.value)}")
    
    dut._log.info("test_edge_triggers passed")
        
@cocotb.test(expect_fail=True)
async def test_should_fail(dut):
    
    dut._log.info("Will fail with msg")

    assert dut.rst_n.value == 0, f"rst_n ({dut.rst_n.value}) == 0"

@cocotb.test(skip=True)
async def test_will_skip(dut):
    dut._log.info("This should not be output!")

# DISABLED cocotb.test(timeout_time=100, timeout_unit='us', expect_fail=True)
async def test_timeout(dut):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await Timer(200, 'us')
    
@cocotb.test()
async def test_timer(dut):
    dut._log.info("Doing nothing but waiting 10ms")
    await Timer(10, units='ms')
    dut._log.info(f"System time is now {get_sim_time('us')}us")
    
def main():
    import microcotb.log as logging
    logging.basicConfig(level=logging.INFO) 
    # import examples.tt_um_factory_test.tt_um_factory_test as ft
    from .loopback import LoopBackCounter
    
    class DUT(LoopBackCounter):
        def __init__(self):
            super().__init__('loopcount')
            # inputs
            self.some_bit = self.new_bit_attribute(self.output, 5)

    # do any required system setup
    
    dut = DUT()
    dut._log.info("enabled loopback/counter project, running")
    runner = cocotb.get_runner()
    runner.test(dut)

if __name__ == '__main__':
    main()
