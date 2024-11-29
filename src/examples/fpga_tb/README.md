## fpga_tb

You can load the verilog for a cocotb testbench onto an FPGA, wrap that in a [SUB](../simple_usb_bridge) layer that allows inspecting and setting signals from the desktop over USB and run the cocotb testbench against that.

So you have:

```
           desktop                                           FPGA
[desktop tests -> microcotb -> DUT w/SUB] <-- USB --> [SUB -> tb.v (project.v etc)]
```

This all presupposes you can get an FPGA running that supports "SUB" wrapped around the tb.v.

More information on doing that side will be provided shortly--keep an eye on this repo and [my youtube channel](https://www.youtube.com/@PsychogenicTechnologies)



