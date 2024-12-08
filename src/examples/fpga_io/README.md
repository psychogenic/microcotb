## fpga_io

You can use an FPGA, configured with the appropriate [SUB](https://github.com/psychogenic/microcotb/tree/main/src/microcotb_sub) fpga_io system to setting and read signals from the desktop over USB and run the cocotb testbench against that.  In this case, the DUT is a black box

So you have:

```
           desktop                                      FPGA         DUT
[desktop tests -> microcotb -> DUT w/SUB] <-- USB --> [SUB IO]  <--> any IC
```

This all presupposes you can get an FPGA running that supports my "SUB" IO for USB control (or something like it).

More information on doing that side will be provided shortly--keep an eye on this repo and [my youtube channel](https://www.youtube.com/@PsychogenicTechnologies)



