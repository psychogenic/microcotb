# microcotb

Copyright &copy; 2024 Pat Deegan [psychogenic.com](https://psychogenic.com)

How do you get hardware-in-the-loop with [cocotb](https://cocotb.org)?  This is one, perhaps weird, answer to that: running cocotb tests right in an RP2040, on the [tinytapeout demoboards](https://github.com/TinyTapeout/tt-micropython-firmware).

This library will run on an [RP2040](https://www.raspberrypi.com/products/rp2040/) and probably anything that runs [micropython](https://www.micropython.org/).

It will also run on the desktop--but then so will cocotb, so what's the point?  The point is getting a simplified manner of extending things to **talk to real hardware**.

The backend will do whatever you want--run on the RP2040 directly, talk over a serial connection or USB, etc.  Whereas the front end provides a cocotb v2 compatible way to detect and run `@cocotb.test()` units just like you did during simulation.

You can 

  * start multiple clocks
  
  * have @cocotb.test()s with attributes, like skip, expect_error, timeout_*
  
  * await on ClockCycles, Timer, RisingEdge, FallingEdge
  
and do most of the usual cocotb things.

One thing it **cannot** do is inspect _internals_ of the DUT, at least not without a lot of help.  In the TinyTapeout case, we only have access to the device as a black box, through the I/O it provides, so unless your bridge to the underlying hardware has some facilities for that it's going to be a blackbox.

For example

```
@cocotb.test()
async def test_counter(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    dut.ui_in.value = 0b1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info("Testing counter")
    for i in range(256):
        assert dut.uo_out.value == dut.uio_out.value, f"uo_out != uio_out"
        assert int(dut.uo_out.value) == i, f"uio value not incremented correctly {dut.uio_out.value} != {i}"
        await ClockCycles(dut.clk, 1)
    dut._log.info("test_counter passed")
    
@cocotb.test()
async def test_edge_triggers(dut):
    dut._log.info("Start")

    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    dut.ui_in.value = 0b1
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    dut._log.info(f"Testing counter, waiting on rising edge of bit 5 at {get_sim_time('us')}us")
    await RisingEdge(dut.some_bit)
    dut._log.info(f"Got rising edge, now {get_sim_time('us')}us value is {hex(dut.uo_out.value)}")
    
    dut._log.info(f"Now await falling edge")
    await FallingEdge(dut.some_bit)
    dut._log.info(f"Got rising edge, now {get_sim_time('us')}us value is {hex(dut.uo_out.value)}")
    
    dut._log.info("test_edge_triggers passed")
```

This is from the [tiny tapeout factory test design](https://github.com/TinyTapeout/tt-micropython-firmware/blob/v2.0-dev/src/examples/tt_um_factory_test/tt_um_factory_test.py).  You'll find more examples in the [examples directory there](https://github.com/TinyTapeout/tt-micropython-firmware/blob/v2.0-dev/src/examples/).

Though not quite as pretty as full cocotb, the tests output logging as usual and provide a summary after the full run

![cocotb test run](images/ucocotb-run.png)


## HIL

With [cocotb](https://cocotb.org), you can test your hardware design while interacting with a simulator.  The website mentions that "interfacing with existing infrastructure is easy. Do you want to talk to a golden model in your testbench? Or to real hardware, e.g. an FPGA or a logic analyzer?"

But the solution to getting our ASIC projects into the loop were pretty involved.  Rather than recreate a "simulator" which provides a whole VPI API that cocotb can interact with, this code was developped to instead make bringing in the testbench to the  on the demo boards easy.

## Quickstart

To get started you need three things:

  1) a set of @cocotb.test()
  
  2) a way to interact with your hardware from python
  
  3) an DUT type that translates reads and writes to signals to the actual hardware
  
  4) an instance of the DUT and to call the runner
  

To dive right in can see a [loopback/counter demo](src/examples/dummy/tb.py) you can run right now by doing

```
>>> import examples.dummy as test
>>> test.run()

# ...
loopcount:1/6 tests failed
loopcount:*** Summary ***
loopcount:      PASS    test_loopback
loopcount:      PASS    test_counter
loopcount:      PASS    test_edge_triggers
loopcount:      PASS    test_should_fail        Failed as expected 
loopcount:      SKIP    test_will_skip
loopcount:      PASS    test_timer
```

  
### @cocotb.test

The cocotb tests should work pretty much as-is (and if not, get in touch).

So a set of things like

```
@cocotb.test(timeout_time=100, timeout_unit='us')
async def test_timeout(dut):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    
    await reset(dut)
    await RisingEdge(dut.is_ready)
```

### talking to hardware

You'll need some manner of getting and setting signals from the hardware.

This could be directly accessed via micropython, as is the case with Tiny Tapeout.  Or it could be over serial, through JTAG, whatever.

For TT demoboards, other than the clock and reset, we have 3 8-bit I/O ports.  It looks [like this](https://github.com/TinyTapeout/tt10-verilog-template/blob/main/src/project.v), in verilog.  One of those is bidirectional, so it's split into _in and _out:

  * ui_in 

  * uo_out

  * uio_in
  
  * uio_out
  

So we've got low-level micropython.native accessors
[like these](https://github.com/TinyTapeout/tt-micropython-firmware/blob/v2.0-dev/src/ttboard/util/platform.py#L114) 

With read_bidir_byte, write_bidir_byte etc in hand, we have a way to communicate with the hardware and get/set the signals.

### DUT

The DUT--device under test--here will need to be created to expose the right interface, in a way that actually gets/sets the hardware.

This library includes a [DUT base class](https://github.com/psychogenic/microcotb/blob/main/src/microcotb/dut.py#L82) for these, which provides some helper functions, setup the *_log* and things like that.

In order for the DUT to be well behaved in your tests, it needs to provide the same interface as it would in cocotb, namely that you play with `dut.attrib.value` a lot.


The Tiny Tapeout DUT implementation looks something like this:

```

class PinWrapper:
    '''
       give bare pins a .value we can assign to
    '''
    def __init__(self, pin):
        self._pin = pin 
        
    @property 
    def value(self):
        return self._pin.value()
    
    @value.setter 
    def value(self, set_to:int):
        if self._pin.mode != Pins.OUT:
            self._pin.mode = Pins.OUT
        self._pin.value(set_to)

class DUT(microcotb.dut.DUT):
    '''
        Tiny Tapeout DUT, providing ui_in, uo_out, and uio_(in|out)
    ''' 
    def __init__(self, name:str='DUT'):
        
        # get the demoboard singleton 
        self.tt = DemoBoard.get()
        
        # wrap the bare clock pin and reset
        self.clk = PinWrapper(self.tt.clk)
        self.rst_n = PinWrapper(self.tt.rst_n)
        self.ena = NoopSignal(1) # does nothing
        
        port_defs = [
            ('uo_out',  8, platform.read_output_byte, None),
            ('ui_in',   8, platform.read_input_byte, platform.write_input_byte),
            ('uio_in',  8, platform.read_bidir_byte, platform.write_bidir_byte),
            ('uio_out', 8, platform.read_bidir_byte, None)
            ]
        for p in port_defs:
            self.add_port(*p)

```

With that DUT, we can run all the TT tests.  It's using wrappers and the `add_port()` method to expose everything in a way that will both interact with the real hardware and go through all the cocotb tests.

### runner

Once you have all the above, simply running

```
    import microcotb as cocotb
    dut = DUT()
    runner = cocotb.get_runner()
    runner.test(dut)
```

will do it's thing.



## DUT class

As mentioned, the DUT instance needs to be able to both talk with the hardware behind the scenes and to act like the cocotb dut.

If you are simply exposing the pins and ports, doing something like the sample above will work fine.

There are cases where tests you have are safe, in that they do not access any internals of the design, but you've added convenience functionality or renaming to the verilog tb, and your cocotb tests reflect that.

For example, [my old neptune testbench](https://github.com/psychogenic/tt04-neptune/blob/main/src/tb.v) looks like this in verilog


```

// testbench is controlled by test.py
module tb (
    input [2:0] clk_config,
    input input_pulse,
    input display_single_enable,
    input display_single_select,
    output [6:0] segments,
    output prox_select
    );

    // this part dumps the trace to a vcd file that can be viewed with GTKWave
    initial begin
        $dumpfile ("tb.vcd");
        $dumpvars (0, tb);
        #1;
    end

    // wire up the inputs and outputs
    reg  clk;
    reg  rst_n;
    reg  ena;
    // reg  [7:0] ui_in;
    reg  [7:0] uio_in;
    wire [7:0] uo_out;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;
    
    assign prox_select = uo_out[7];
    assign segments = uo_out[6:0];
    
    wire [7:0] ui_in = {display_single_select, 
                        display_single_enable, 
                        input_pulse, 
                        clk_config[2], clk_config[1], clk_config[0],
                        1'b0,1'b0};

   /* ... */
```

and my cocotb tests use the nicely named `input_pulse` (a bit), `clk_config` (3 bits), etc.

The first option would be to re-write all the cocotb.test() stuff to use only ui_in and such.  Yuk.

Rather than do all that work, and have ugly `tt.ui_in.value[5]` stuff everywhere as a bonus, you can extend the DUT class to add in wrappers to these values.

To do this, you just derive a new class from `microcotb.dut.DUT`, create the attributes using `new_bit_attribute` or `new_slice_attribute` (for things like `tt.ui_in[3:1]`).

In my neptune case, this looks like:

```
# using the ttboard extension of the DUT as the
# baseclass, which already provides ui_in, uo_out, etc
import ttboard.cocotb.dut

class DUT(ttboard.cocotb.dut.DUT):
    def __init__(self):
        super().__init__('Neptune')
        self.tt = DemoBoard.get()
        # inputs
        self.display_single_select = self.new_bit_attribute(self.tt.ui_in, 7)
        self.display_single_enable = self.new_bit_attribute(self.tt.ui_in, 6)
        self.input_pulse = self.new_bit_attribute(self.tt.ui_in, 5)
        self.clk_config = self.new_slice_attribute(self.tt.ui_in, 4, 2) # tt.ui_in[4:2]
        # outputs
        self.prox_select = self.new_bit_attribute(self.tt.uo_out, 7)
        self.segments = self.new_slice_attribute(self.tt.uo_out, 6, 0) # tt.uo_out[6:0]
````

Using that class to construct my dut, things like

```

    pulseClock = Clock(dut.input_pulse, 1000*(1.0/tunerInputFreqHz), units='ms')
    cocotb.start_soon(pulseClock.start())
    # or
    val = int(dut.segments.value) << 1
```

will justwork(tm) in the tests.
     


## License

This library is release under the LGPL.  See the LICENSE files for details.
Certain portions were adapted from [cocotb](https://cocotb.org) (namely found in microcotb.types) to run on uPython and extend them, and are 

Copyright cocotb contributors

and under the

Licensed under the Revised BSD License, see LICENSE for details.
SPDX-License-Identifier: BSD-3-Clause

See individual files.
