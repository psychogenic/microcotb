'''
Created on Dec 2, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.clock import Clock
from microcotb.triggers import ClockCycles 
import microcotb as cocotb
import microcotb.log as logging
from microcotb.time.system import SystemTime
from microcotb.time.value import TimeValue
from microcotb.triggers.edge import RisingEdge

from microcotb.utils import get_sim_time

from examples.simple_usb_bridge.dut_sub import DUT, DefaultPort


cocotb.set_runner_scope(__name__)


async def reset_and_enable(dut, reset_hold_time:int=50):
    
    # startup disabled
    dut.start_address.value = 0 # beginning of flash
    dut.enable.value = 0
    dut.rst.value = 1
    await ClockCycles(dut.clk, reset_hold_time)
    dut.rst.value = 0
    await ClockCycles(dut.clk, reset_hold_time)
    
    # enable
    dut.enable.value = 1
    await ClockCycles(dut.clk, 2)
    # we should startup without a valid value
    assert dut.value_valid.value == 0, "Valid value already asserted"
    
    

async def ack_register_rcvd(dut):
    
    dut._log.debug("ACK reg processed")
    await ClockCycles(dut.clk, 5)
    
    dut.register_processed.value = 1
    await ClockCycles(dut.clk, 1)
    dut.register_processed.value = 0
    await ClockCycles(dut.clk, 1)

@cocotb.test()
@cocotb.parametrize(
    ('mon_full', [False, True])
)
async def test_monitorcontrol(dut:DUT, mon_full:bool):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    # say we know we can reset and get 
    # a fresh sample... skip logging
    if mon_full:
        dut._log.info("Test with monitoring throughout")
    else:
        dut._log.info("Test with monitoring suspended at first")
    dut.is_monitoring = mon_full 
    # and get there
    await reset_and_enable(dut, 50)
    await RisingEdge(dut.fresh_sample)
    
    # now the area of interest, monitor back on
    dut._log.info("now wait on value_valid...")
    await RisingEdge(dut.value_valid)
    
    dut.is_monitoring = True 
    dut._log.info("Got fresh reg set!!")
    await ack_register_rcvd(dut)
    await ClockCycles(dut.clk, 60)
    


@cocotb.test(timeout_time=40, timeout_unit='ms')
async def test_firstvalid_time(dut):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    await reset_and_enable(dut)
    
    assert dut.fresh_sample.value == 0, "Already had a fresh sample??"
    
    dut._log.info("Waiting on fresh_sample, first one takes a while...")
    await RisingEdge(dut.fresh_sample)
    dut._log.info("now wait on value_valid...")
    await RisingEdge(dut.value_valid)
    t_now = get_sim_time('ms')
    assert t_now < 20, f"Took too long {t_now}ms to get first valid"
    
    await ClockCycles(dut.clk, 10)
    
    dut._log.info("Testing reset...")
    await reset_and_enable(dut)
    
    assert dut.fresh_sample.value == 0, "still have fresh sample?"
    assert dut.value_valid.value == 0, "still have validu valid?"
    
    await RisingEdge(dut.value_valid)
    
    
def dump_reg_setting(dut):
    dut._log.info(f"    Got valid reg ({hex(dut.register.value)}/{hex(dut.register_value.value)})")
    
@cocotb.test(timeout_time=300, timeout_unit='ms')
async def test_parse(dut:DUT):
    samples_in_reg_set = [16, 4, 3, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1]
    num_samples = 11 # number of registers to fetch
    reg_set = 0
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    
    # don't log this test, go faster
    #dut.write_vcd_enabled = False
    #dut.is_monitoring = False
    
    await reset_and_enable(dut)
    
    # now it'll read in the file header
    dut._log.info("Waiting on first fresh sample, takes a while...")
    await RisingEdge(dut.fresh_sample)
    dut._log.info(f"Got it, elapse sim time is {SystemTime.current()}, clocking in {num_samples} registers")
    
    
    while reg_set < num_samples:
        
        if dut.fresh_sample.value == 1:
            while not int(dut.value_valid.value):
                await ClockCycles(dut.clk, 2)
                
            
            dut._log.info("Got fresh reg set!!")
            assert dut.registers_in_sample.value == samples_in_reg_set[reg_set], f"for {reg_set+1} have {int(dut.registers_in_sample.value)} regs in samp"
            dut._log.info(f"Set {reg_set+1} does indeed have {samples_in_reg_set[reg_set]} settings")
            
            num_regs = 1
            reg_set += 1
            
            # dump_reg_setting(dut)
            await ack_register_rcvd(dut)
            continue
            
        
        if not int(dut.value_valid.value):
            await RisingEdge(dut.value_valid)
            dut._log.debug(f"GOT RISING EDGE ON value_valid")
                
                
        dump_reg_setting(dut)
        await ack_register_rcvd(dut)
        num_regs += 1
        

def main(dut:DUT = None):
    TimeValue.ReBaseStringUnits = True
    logging.basicConfig(level=logging.INFO)
    runner = cocotb.get_runner(__name__)
    if dut is None:
        dut = getDUT()
    dut._log.info(f"enabled SPI Parser (PSYM Reader) project, will test with {runner}")
    
    # get state changes asynchronously:
    dut.is_monitoring = True
    # write a VCD for every test run
    dut.write_test_vcds_to_dir = '/tmp'
    dut.write_vcd_enabled = True
    
    # run them tests
    runner.test(dut)


def getDUT(serial_port:str=DefaultPort, name:str='PSYMrdr'):
    dut = DUT(serial_port, name, auto_discover=True)
    dut.asynchronous_events = True
    return dut

if __name__ == '__main__':
    main()
