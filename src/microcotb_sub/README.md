# SUB Sample

This sample shows how I ran the [neptune](https://github.com/psychogenic/tt04-neptune/) [testbench](../fpga_tb/neptune_tb.py)(adapted [from here](https://github.com/psychogenic/tt04-neptune/blob/main/src/test.py)) on an FPGA that includes and exposes [this verilog testbench](https://github.com/psychogenic/tt04-neptune/blob/main/src/tb.v).

To do this, an FPGA wraps the [tb.v](https://github.com/psychogenic/tt04-neptune/blob/main/src/tb.v) (which in turn includes the [verilog from the actual project](https://github.com/psychogenic/tt04-neptune/blob/main/src/neptune_tinytapeout_propwindow.v)) in a layer that implement the "SUB".

Though we are going through a USB serial connection to interact with the hardware from the desktop, this is actually 10x faster than running under micropython.

## SUB: Simple USB Bridge 

For this to work, you need an FPGA that includes the testbench (which in turn includes the project) and wraps all that up with a layer that allows listing and r/w access to the signals in the tb.v device under test.

That top layer implements the "Simple USB Bridge" to accept USB serial connections and respond to commands to list, read and write signals.  I have this all running on a lattice up5k at the moment.



## DUT implementation

The [dut](./dut.py) class implements a decent base class that may also be used as-is.

Each discovered signal has a `.value` that may be used, including with indices and slices assuming its width permits it.

Read and writes to a dut signal's `.value` and transparently transported over serial to the SUB layer on an FPGA.

### example REPL interaction

```
>>> from microcotb_sub.dut import *
>>> dut = DUT('/dev/ttyACM0', name='myDUT',  auto_discover=True)
>>> dut.host.value
<LogicArray('00000000', Range(7, 'downto', 0))>
>>> dut.host.value[4:2] = 0b101
>>> dut.host.value[4:2]
<LogicArray('101', Range(4, 'downto', 2))>
>>> dut.host.value
<LogicArray('00010100', Range(7, 'downto', 0))>
>>> dut.clk.value = 1
>>> dut.clk.value
<LogicArray('1', Range(0, 'downto', 0))>
>>> int(dut.clk.value)
1
>>> dut.clk.value > 0
True
```

## SUB Protocol

My Simple USB Bridge protocol is dumb and slow, and more a proof of concept than anything, but it still provides read or write access to

  * up to 16 single bit signals, quickly
  
  * up to 32 multi-bit signals (limited to 8 bits as it now stands), using a slightly longer transfer for write operations
  
and allows for automatic signal discovery, meaning the DUT on the FPGA is queried for the list of signals available.

Everything happens over USB serial, with communications initiated by the desktop side.

Each transfer sends at least one byte of the form `0bINAAAAVR`, where

```
  0bINAAAAVR
    I == 0 for commands, I == 1 for I/O interaction
     N == 1 for multi-bit signals
     0AAAA  4-bit address for single bit signals
     1AAAAV 5-bit address for multi-bit signals
          V in the case of single bit signal writes, the value is set on this bit
           R == 1 I/O read, write otherwise
```

I/O reads will transfer the value, as a raw byte, over USB serial.

For single bit reads, the value is passed along with the address of the signal in question.
For multi-bit signals, writes involve sending a second byte with the actual value.

This allows the cocotb testbench to toggle the project clock (and other single-bit signals) with a write of a single byte over USB.

You can see this in operation in the [DUT](./dut.py) and [Signal](./signal.py) implementations here.

I'll be publishing the FPGA side of this in the near future.

### Listing Signals

The SUB protocol implemented also includes a method of discovering which signals are actually available.

This is implemented as [dut discover()](./dut.py#L82).  By sending a `b'l'` over USB, the SUB will respond with a list of attributes, sending one entry per line.

Each entry is separated by `|` and has the form

```
name~DETAILS
Where
 DETAILS is 2 bytes: ADDRESS and DESCRIPTION
  ADDRESS: the address to read/write to for the signal (high bit indicates multi-bit)
  DESCRIPTION:  
   DESCRIPTION[7] (high bit) is_input: if 1, this can be written to
   DESCRIPTION[6:0] signal bit width
```

Calling `discover()` on the DUT implementation or its derivatives will fetch this data and setup attributes accordingly.

### Value Change Notifications

Changes may occur on the DUT side to values, pretty much any time.  If monitoring is activated, these changes will be sent over using a simple protocol where `b'm'` indicates the start of a monitoring packet, followed by

```
  STARTBYTE [PAYLOADBYTE]
    STARTBYTE is either
       * SINGLEBITVALUE;
       * MULTIBIT_ADDRESS; or
       * END_OF_STREAM.
    SINGLEBITVALUE is a combo address and value for a single-bit signal.
    SINGLEBITVALUE is comprised of the new value in the MSB and the 
                 signal address is the [3:0] LSB, where the two, 
                 so  V000AAAA
                 
    MULTIBIT_ADDRESS is the address of a wide signal.  It is always followed
    by a PAYLOADBYTE.
    MULTIBIT_ADDRESS will always be >= 32, ie.
    0b100000, so its address always has the form
    001AAAAA.  These address require a 2nd byte, the new VALUE.
    
    END_OF_STREAM is simply 0xff
```

The SerialStream and SUBStateChangeReport collaborate to manage the asynchronous events coming in, such that complete VCD files can be produced.
 
  



## Samples

See [fpga_tb](../fpga_tb/) for examples of talking to an FPGA that wraps a project/testbench module with a SUB layer to expose the signals over USB.  Cool thing about this is being able to expose state deep within submodules to inspection, VCD dumps etc.

See [fpga_io](../fgpa_io/) for an example of talking *through* an FPGA, to control its I/O and run tests on any external chip.  The advantage there is that its completely hardware agnostic--you can test anything you can wire the FPGA bridge to.

With the neptune project under the SUB wrapper on the FPGA, running

```
$ time python examples/fpga_tb/tb.py

```

results in output like

```
INFO:SUB:enabled neptune project, will test with Runner with 3 test cases:
        <TestCase note_e_highfar>
        <TestCase note_g_highclose>
        <TestCase note_a_exact>
INFO:microcotb_sub.dut:SUB DUT performing discovery
INFO:microcotb_sub.dut:Have signal clk at 0
INFO:microcotb_sub.dut:Have signal rst_n at 1
INFO:microcotb_sub.dut:Have signal ena at 2
INFO:microcotb_sub.dut:Have signal input_pulse at 3
INFO:microcotb_sub.dut:Have signal display_single_enable at 4
INFO:microcotb_sub.dut:Have signal display_single_select at 5
INFO:microcotb_sub.dut:Have signal prox_select at 6
INFO:microcotb_sub.dut:Have signal clk_config at 32
INFO:microcotb_sub.dut:Have signal segments at 33
INFO:SUB:*** Running Test 1/3: note_e_highfar ***
INFO:SUB:E @ 330 delta 12
INFO:SUB:little E high/far
INFO:SUB:starting clock
INFO:SUB:reset(dut)
INFO:SUB:hold in reset
INFO:SUB:reset done
INFO:SUB:Note E @ 330 pass (0b10011110)
INFO:SUB:Note E full pass
WARNING:SUB:*** Test 'note_e_highfar' PASS ***

...

INFO:SUB:Note A pass (0b11101110)
INFO:SUB:Note A full pass
WARNING:SUB:*** Test 'note_a_exact' PASS ***
INFO:SUB:All 3 tests passed
INFO:SUB:*** Summary ***
WARNING:SUB:    PASS    note_e_highfar
WARNING:SUB:    PASS    note_g_highclose
WARNING:SUB:    PASS    note_a_exact

real    0m5.588s
user    0m0.311s
sys     0m0.221s
```


There's also a version of [Matt's RGB Mixer](https://github.com/mattvenn/tt06-rgb-mixer/tree/cocotb_hw_in_loop/test) in [rgbmix_test.py](../fpga_tb/rgbmix_test.py).

With that testbench on the FPGA, wrapped in the SUB to expose the signals over serial, you can do

```

time python examples/simple_usb_bridge/rgbmix_test.py

```

and get it to complete

```

INFO:RGBMX:let noisy transition finish
INFO:RGBMX:Done
WARNING:RGBMX:*** Test 'test_enc2' PASS ***
INFO:RGBMX:*** Running Test 4/4: test_finishoff ***
INFO:RGBMX:sync to PWM
INFO:RGBMX:now wait for falling clock
INFO:RGBMX:Should all be on for max_count
ERROR:RGBMX:*** Test 'test_finishoff' FAIL: pwm1_out is 0 on clock 0 ***
WARNING:RGBMX:1/4 tests failed
INFO:RGBMX:*** Summary ***
WARNING:RGBMX:  PASS    test_enc0
WARNING:RGBMX:  PASS    test_enc1
WARNING:RGBMX:  PASS    test_enc2
ERROR:RGBMX:    FAIL    test_finishoff  pwm1_out is 0 on clock 0

real    1m33.930s
user    0m1.784s
sys     0m1.455s
```

Though that last test is failing, for reasons unknown.


