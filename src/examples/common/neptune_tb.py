'''
Created on Nov 28, 2024

Adapted from https://github.com/TinyTapeout/tt-micropython-firmware/blob/v2.0-dev/src/examples/tt_um_psychogenic_neptuneproportional/tt_um_psychogenic_neptuneproportional.py
originally
https://github.com/psychogenic/tt04-neptune/blob/main/src/test.py


@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.clock import Clock
from microcotb.triggers import Timer, ClockCycles # RisingEdge, FallingEdge, Timer, ClockCycles
import microcotb as cocotb
OnlyLast = False
DefaultToggleTime = 0.515
displayNotes = {
            'NA':     0b00000010, # -
            'A':      0b11101110, # A
            'B':      0b00111110, # b
            'C':      0b10011100, # C
            'D':      0b01111010, # d
            'E':      0b10011110, # E
            'F':      0b10001110, # F
            'G':      0b11110110, # g
            }
            
displayProx = {
            'lowfar':       0b00111000,
            'lowclose':     0b00101010,
            'exact':        0b00000001,
            'hiclose':      0b01000110,
            'hifar':        0b11000100

}

SegmentMask = 0xFF
ProxSegMask = 0xFE

class ClockFreq:
    Clock1KHz = 0
    Clock2KHz = 1
    Clock4KHz = 2
    Clock3277Hz = 3 # 32.768k / 10
    Clock10KHz = 4
    Clock32KHz = 5 # 32.768k
    Clock40KHz = 6
    Clock60KHz = 7
    
SelectedClockFreq = ClockFreq.Clock4KHz
    
ClockConfig = {
    
    ClockFreq.Clock1KHz: {
            'config': ClockFreq.Clock1KHz,
            'freq': 1000,
        },
    ClockFreq.Clock2KHz: {
        
            'config': ClockFreq.Clock2KHz,
            'freq': 2000,
        },
    
    ClockFreq.Clock4KHz: {
        
            'config': ClockFreq.Clock4KHz,
            'freq': 4000,
        },
    ClockFreq.Clock10KHz: {
        
            'config': ClockFreq.Clock10KHz,
            'freq': 10000,
        },
    ClockFreq.Clock40KHz: {
        
            'config': ClockFreq.Clock40KHz,
            'freq': 40000,
        }
}

async def reset(dut, clock_freq=SelectedClockFreq):
    dut._log.info(f"reset(dut)")
    dut.display_single_enable.value = 0
    dut.display_single_select.value = 0
    dut.rst_n.value = 0
    dut.clk_config.value = ClockConfig[clock_freq]['config']
    dut._log.info("hold in reset")
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    
    dut._log.info("reset done")
   
    
async def startup(dut, clock_freq=SelectedClockFreq):
    dut._log.info("starting clock")
    
    freqHz = ClockConfig[clock_freq]['freq']
    
    periodUs = int(1e6/freqHz)
    clock = Clock(dut.clk, periodUs, units="us")
    cocotb.start_soon(clock.start())
    dut._log.info(f"resetting, with system clock @ {freqHz}Hz")
    await reset(dut, clock_freq)
    dut.input_pulse.value = 0
            
async def getDisplayValues(dut):
    displayedValues = [None, None]
    attemptCount = 0
    while None in displayedValues or attemptCount < 3:
        displayedValues[int(dut.prox_select.value)] = int(dut.segments.value) << 1
        
        await ClockCycles(dut.clk, 1)
        
        attemptCount += 1
        if attemptCount > 100:
            dut._log.error(f"NEVER HAVE {displayedValues}")
            return displayedValues
            
    # dut._log.info(f'Display Segments: {displayedValues} ( [ {bin(displayedValues[0])} , {bin(displayedValues[1])}])')
    return displayedValues
    
async def inputPulsesFor(dut, tunerInputFreqHz:int, inputTimeSecs=0.51):
    ms_per = (1000.0/tunerInputFreqHz)
    dut._log.info(f"Starting pulse in clocking at {tunerInputFreqHz} Hz (per: {ms_per:.3f}ms)")
    pulseClock = Clock(dut.input_pulse, ms_per, units='ms')
    cocotb.start_soon(pulseClock.start())

    await Timer(inputTimeSecs, 'sec')
    dispV = await getDisplayValues(dut)
    
    return dispV
    


async def setup_tuner(dut):
    dut._log.info("start")
    await startup(dut)
    

async def note_toggle(dut, freq, delta=0, msg="", toggleTime=DefaultToggleTime, skip_reset:bool=False):
    dut._log.info(msg)
    if not skip_reset:
        await startup(dut)
    dut._log.info('startup done')
    dispValues = await inputPulsesFor(dut, freq + delta, toggleTime)  
    return dispValues
    
    

async def note_e(dut, eFreq=330, toggleTime=DefaultToggleTime, delta=0, msg=""):
    dut._log.info(f"E @ {eFreq} delta {delta}")
    dispValues = await note_toggle(dut, freq=eFreq, toggleTime=toggleTime, delta=delta, msg=msg)
    note_target = (displayNotes['E'] & SegmentMask)
    assert dispValues[1] == note_target, f"Note E FAIL: {dispValues[1]} != {note_target}"
    dut._log.info(f"Note E @ {eFreq} pass ({bin(dispValues[1])})")
    return dispValues


    
@cocotb.test(skip=OnlyLast)
async def note_e_highfar(dut):
    dispValues = await note_e(dut, eFreq=330, delta=12, msg="little E high/far")
    target_value =  (displayProx['hifar'] & ProxSegMask)
    assert dispValues[0] == target_value, f"high/far fail {dispValues[0]} != {target_value}"
    dut._log.info("Note E full pass")



async def note_g(dut, delta=0, msg=""):
    gFreq = 196
    
    dut._log.info(f"G delta {delta}")
    dispValues = await note_toggle(dut, freq=gFreq, delta=delta, msg=msg);
    
    note_target = (displayNotes['G'] & SegmentMask)
    assert dispValues[1] == note_target, f"Note G FAIL: {dispValues[1]} != {note_target}"
    dut._log.info(f"Note G: PASS ({bin(dispValues[1])})")
    return dispValues

@cocotb.test(skip=OnlyLast)
async def note_g_highclose(dut):
    dispValues = await note_g(dut, delta=3, msg="High/close")
    target_value =  (displayProx['hiclose'] & ProxSegMask)
    assert dispValues[0] == target_value, f"High/close fail {dispValues[0]} != {target_value}"
    dut._log.info("Note G full pass")
    


async def note_a(dut, delta=0, msg="", toggleTime=DefaultToggleTime, skip_reset:bool=False):
    aFreq = 110
    
    dut._log.info(f"A delta {delta}")
    dispValues = await note_toggle(dut, freq=aFreq, delta=delta, msg=msg, 
                                   toggleTime=toggleTime, skip_reset=skip_reset);
    
    note_target = (displayNotes['A'] & SegmentMask)
    assert dispValues[1] == note_target, f"Note A FAIL: {dispValues[1]} != {note_target}"
    dut._log.info(f"Note A pass ({bin(dispValues[1])})")
    return dispValues

@cocotb.test(skip=OnlyLast)
@cocotb.parametrize(
    ("clocking", [
        ClockFreq.Clock1KHz,
        ClockFreq.Clock2KHz,
        ClockFreq.Clock4KHz
        ]), 
)
async def note_a_exact(dut, clocking):
    # handle startup/reset ourselves, so we can play with clocking
    await startup(dut, clocking)
    dispValues = await note_a(dut, delta=0, toggleTime=DefaultToggleTime*2, msg="A exact", skip_reset=True)
    
    target_value =  (displayProx['exact'] & ProxSegMask)
    assert dispValues[0] == target_value, f"exact fail {dispValues[0]} != {target_value}"
    dut._log.info("Note A full pass")
    
    
    
    
    
    
    
    
    
    
    
async def note_b(dut, delta=0, msg=""):
    gFreq = 246.5
    
    dut._log.info(f"B delta {delta}")
    dispValues = await note_toggle(dut, freq=gFreq, delta=delta, msg=msg);
    assert dispValues[1] == (displayNotes['B'] & SegmentMask)
    return dispValues
    

 

    
@cocotb.test(skip=OnlyLast)
async def note_fatE_lowfar(dut):
    dispValues = await note_e(dut, eFreq=83, toggleTime=DefaultToggleTime*2, delta=-4, msg="fat E low/far")
    assert (dispValues[0] == (displayProx['lowfar'] & ProxSegMask)) or (dispValues[0] == (displayProx['exact'] & ProxSegMask))
    
    
 
@cocotb.test(skip=OnlyLast)
async def note_fatE_exact(dut):
    dispValues = await note_e(dut, eFreq=83, toggleTime=DefaultToggleTime*2, delta=-1, msg="fat E -1Hz")
    assert dispValues[0] == (displayProx['exact'] & ProxSegMask)
    
@cocotb.test(skip=OnlyLast)
async def note_e_lowclose(dut):
    dut._log.info("NOTE: delta same as for fat E, but will be close...")
    dispValues = await note_e(dut, eFreq=330, delta=-7, msg="E exact")
    assert dispValues[0] == (displayProx['lowclose'] & ProxSegMask) 


    
@cocotb.test(skip=OnlyLast)
async def note_e_exact(dut):
    dispValues = await note_e(dut, eFreq=330, delta=0, msg="E exact")
    assert dispValues[0] == (displayProx['exact'] & ProxSegMask) 

    

@cocotb.test(skip=OnlyLast)
async def note_g_lowclose(dut):
    dispValues = await note_g(dut, delta=-4, msg="G low/close")
    assert dispValues[0] == (displayProx['lowclose'] & ProxSegMask) 
   

    
@cocotb.test(skip=OnlyLast)
async def note_g_lowfar(dut):
    dispValues = await note_g(dut, delta=-10, msg="G low/far")
    assert dispValues[0] == (displayProx['lowfar'] & ProxSegMask) 
    
     

@cocotb.test(skip=OnlyLast)
async def note_a_highfar(dut):
    dispValues = await note_a(dut, delta=4, msg="A high/far")
    assert dispValues[0] == (displayProx['hifar'] & ProxSegMask) 
   



@cocotb.test(skip=OnlyLast)
async def note_b_high(dut):
    dispValues = await note_b(dut, delta=4, msg="B high/close")
    assert dispValues[0] == (displayProx['hiclose'] & ProxSegMask) 
 


## @cocotb.test(skip=OnlyLast)
async def note_b_exact(dut):
    dispValues = await note_b(dut, delta=0, msg="B exact")
    targ_value = (displayProx['exact'] & ProxSegMask)
    assert dispValues[0] == targ_value, f"got note B but not exact? ({dispValues[0]} != {targ_value})"
 


@cocotb.test(skip=OnlyLast)
async def success_test(dut):
    await note_toggle(dut, freq=20, delta=0, msg="just toggling -- end");
    

@cocotb.test()
async def note_e_then_a(dut):
    
    dut.is_monitoring = True
    dut.write_vcd_enabled = True
    dut._log.info("NOTE: delta same as for fat E, but will be close...")
    dispValues = await note_e(dut, eFreq=330, delta=-2, msg="E exact")
    assert dispValues[0] == (displayProx['exact'] & ProxSegMask) 
    
    
    dispValues = await note_a(dut, delta=0, msg="A exact", toggleTime=1.1, skip_reset=True)
    
    target_value =  (displayProx['exact'] & ProxSegMask)
    assert dispValues[0] == target_value, f"exact fail {dispValues[0]} != {target_value}"
    dut._log.info("Note A full pass")
    

    