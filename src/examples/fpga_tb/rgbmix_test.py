'''
Adapted from https://github.com/mattvenn/tt06-rgb-mixer/tree/main/test
by Matt Venn
'''
import microcotb as cocotb
from microcotb.clock import Clock
from microcotb.triggers import RisingEdge, FallingEdge, ClockCycles
from examples.fpga_tb.rgbmix_encoder import Encoder

clocks_per_phase = 10
max_count = 255

async def reset(dut):
    dut.enc0_a.value = 0
    dut.enc0_b.value = 0
    dut.enc1_a.value = 0
    dut.enc1_b.value = 0
    dut.enc2_a.value = 0
    dut.enc2_b.value = 0
    dut.rst_n.value   = 0

    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1;
    await ClockCycles(dut.clk, 5) # how long to wait for the debouncers to clear
    
    
    dut._log.info("DUT is reset")

    # pwm should all be low at start
    assert dut.pwm0_out.value == 0
    assert dut.pwm1_out.value == 0
    assert dut.pwm2_out.value == 0

async def run_encoder_test(dut, encoder, mx_count):
    
    update_num = clocks_per_phase * 2 * mx_count
    dut._log.info(f"Will update {update_num} times")
    for i in range(update_num):
        if (i+1) % 500 == 0:
            dut._log.info(f'Update {i+1}')
        else:
            dut._log.debug("update")
        await encoder.update(1)

    # let noisy transition finish, otherwise can get an extra count
    dut._log.info('let noisy transition finish')
    for i in range(10):
        dut._log.debug("update")
        await encoder.update(0)
    dut._log.info('Done')
    v = dut.debug_enc.value
    assert v == max_count, f"{v} should == {max_count}"


async def test_encoder(dut, e:Encoder, dbg_mode:int):
   
    # do 3 ramps for each encoder 
    dut.debug_mode.value = dbg_mode
    dut._log.info(f"run encoder{dbg_mode} test")
    await run_encoder_test(dut, e,  max_count)
    
@cocotb.test()
async def test_enc0(dut):
    # only starting clock in 1st test, in order to accumulate state
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    await reset(dut)
    
    enc = Encoder(dut, dut.clk, dut.enc0_a, dut.enc0_b, clocks_per_phase = clocks_per_phase, noise_cycles = clocks_per_phase / 4)
    
    await test_encoder(dut, enc, 0)
    

@cocotb.test()
async def test_enc1(dut):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    enc = Encoder(dut, dut.clk, dut.enc1_a, dut.enc1_b, clocks_per_phase = clocks_per_phase, noise_cycles = clocks_per_phase / 4)
    
    await test_encoder(dut, enc, 1)
    

@cocotb.test()
async def test_enc2(dut):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    enc = Encoder(dut, dut.clk, dut.enc2_a, dut.enc2_b, clocks_per_phase = clocks_per_phase, noise_cycles = clocks_per_phase / 4)

    await test_encoder(dut, enc, 2)
    
@cocotb.test()
async def test_finishoff(dut):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut._log.info("sync to PWM")
    # sync to pwm
    await RisingEdge(dut.pwm0_out)
    dut._log.info("now wait for falling clock")
    await FallingEdge(dut.clk)
    await ClockCycles(dut.clk, 1)
    # pwm should all be on for max_count 
    dut._log.info("Should all be on for max_count")
    for i in range(max_count - 1): 
        assert dut.pwm0_out.value == 1, f"pwm0_out is {dut.pwm0_out.value} on clock {i}"
        assert dut.pwm1_out.value == 1, f"pwm1_out is {dut.pwm1_out.value} on clock {i}"
        assert dut.pwm2_out.value == 1, f"pwm2_out is {dut.pwm2_out.value} on clock {i}"
        await ClockCycles(dut.clk, 1)



import logging
from examples.simple_usb_bridge.dut import DUT
def main():
    logging.basicConfig(level=logging.INFO)
    runner = cocotb.get_runner()
    dut = DUT('/dev/ttyACM0', 'RGBMX')
    dut._log.info(f"enabled rgbmixer project, will test with {runner}")
    runner.test(dut)


if __name__ == '__main__':
    main()

