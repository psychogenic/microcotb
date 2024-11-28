## SUB Sample

This sample shows how I ran the [neptune](https://github.com/psychogenic/tt04-neptune/) [testbench](./tb.py)(adapted [from here](https://github.com/psychogenic/tt04-neptune/blob/main/src/test.py)) on an FPGA that includes and exposes [this verilog testbench](https://github.com/psychogenic/tt04-neptune/blob/main/src/tb.v).

To do this, an FPGA wraps the [tb.v](https://github.com/psychogenic/tt04-neptune/blob/main/src/tb.v) (which in turn includes the [verilog from the actual project](https://github.com/psychogenic/tt04-neptune/blob/main/src/neptune_tinytapeout_propwindow.v)) in a layer that implement the "SUB".

Though we are going through a USB serial connection to interact with the hardware from the desktop, this is actually 10x faster than running under micropython.

### SUB: Simple USB Bridge 

My Simple USB Bridge provides read or write access to

  * up to 16 single bit signals, quickly
  
  * up to 32 multi-bit signals, using a slightly longer transfer for write operations
  
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


You can see this in operation in the [DUT and Signal](./dut.py) implementation here.

### Sample

With the neptune project under the SUB wrapper on the FPGA, running

```
$ time python examples/simple_usb_bridge/tb.py

```

results in output like

```
INFO:SUB:enabled neptune project, will test with Runner with 3 test cases:
        <TestCase note_e_highfar>
        <TestCase note_g_highclose>
        <TestCase note_a_exact>
INFO:examples.simple_usb_bridge.dut:SUB DUT performing discovery
INFO:examples.simple_usb_bridge.dut:Have signal clk at 0
INFO:examples.simple_usb_bridge.dut:Have signal rst_n at 1
INFO:examples.simple_usb_bridge.dut:Have signal ena at 2
INFO:examples.simple_usb_bridge.dut:Have signal input_pulse at 3
INFO:examples.simple_usb_bridge.dut:Have signal display_single_enable at 4
INFO:examples.simple_usb_bridge.dut:Have signal display_single_select at 5
INFO:examples.simple_usb_bridge.dut:Have signal prox_select at 6
INFO:examples.simple_usb_bridge.dut:Have signal clk_config at 32
INFO:examples.simple_usb_bridge.dut:Have signal segments at 33
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


There's also a version of [Matt's RGB Mixer](https://github.com/mattvenn/tt06-rgb-mixer/tree/cocotb_hw_in_loop/test) in [rgbmix_test.py](./rgbmix_test.py).

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

