'''
Created on Dec 2, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from examples.fpga_io.tt_dut import TinyTapeoutDUT
import microcotb.log as logging
from microcotb.time.value import TimeValue
import microcotb as cocotb
from microcotb.clock import Clock
from microcotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
from microcotb.utils import get_sim_time

cocotb.set_runner_scope(__name__)

@cocotb.test()
async def test_loopback(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1

    # RP is is writing to bidirs
    dut.uio_oe.value = 0xff # all outputs from us, 
    dut.ui_in.value = 0b0
    dut.uio_in.value = 0
    # do reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    
    # see that value written to bidirs is reflected out
    for i in range(256):
        dut.uio_in.value = i
        await ClockCycles(dut.clk, 1)
        assert dut.uo_out.value == i, f"uio value unstable {dut.uio_out.value} != {i}"

    dut._log.info("test_loopback passed")

@cocotb.test()
async def test_counter(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # RP reading bidirs
    dut.uio_oe.value = 0 # all inputs on our side
    
    dut.ui_in.value = 0b1
    # do reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    
    # se that counter goes up by 1 every cycle
    dut._log.info("Testing counter")
    for i in range(256):
        assert dut.uo_out.value == dut.uio_out.value, f"uo_out != uio_out"
        assert int(dut.uo_out.value) == i, f"uio value not incremented correctly {dut.uio_out.value} != {i}"
        await ClockCycles(dut.clk, 1)
        
    
    dut._log.info("test_counter passed")
    

@cocotb.test(expect_fail=True)
async def test_should_fail(dut):
    
    dut._log.info("Will fail with msg")

    assert dut.rst_n.value == 0, f"rst_n ({dut.rst_n.value}) == 0"
    
@cocotb.test(skip=True)
async def test_will_skip(dut):
    dut._log.info("This should not be output!")


@cocotb.test(timeout_time=100, timeout_unit='us', expect_fail=True)
@cocotb.parametrize(
    ("clk_period", [10,125]), 
    ("timer_t", [101,200])
)
async def test_timeout(dut, clk_period:int, timer_t:int):
    clock = Clock(dut.clk, clk_period, units="us")
    cocotb.start_soon(clock.start())
    # will timeout before the timer expires, hence expect_fail=True above
    await Timer(timer_t, 'us')
    
 
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
