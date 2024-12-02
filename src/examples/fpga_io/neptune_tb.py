'''
Created on Nov 29, 2024

Adapted from https://github.com/TinyTapeout/tt-micropython-firmware/blob/v2.0-dev/src/examples/tt_um_psychogenic_neptuneproportional/tt_um_psychogenic_neptuneproportional.py
originally
https://github.com/psychogenic/tt04-neptune/blob/main/src/test.py

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import logging
import examples.fpga_tb.neptune_tb as neptune_tb
import examples.fpga_io.tt_dut as tt_dut

class NeptuneDUT(tt_dut.TinyTapeoutDUT):
    '''
        Rather than setup neptune-specific signal mappings on the FPGA,
        doing it here allows a single I/O-through SUB FPGA to work with 
        *any* tiny tapeout project.
        
        So the base class DUT will expose ui_in, uo_out etc for all projects,
        and here we create named attributes using bits and slices from those
        standard signals, that are used in the testbench.
    '''
    def __init__(self, serial_port:str):
        super().__init__(serial_port, 'Neptune', auto_discover=True)
        # inputs
        self.display_single_select = self.new_bit_attribute(self.ui_in, 7)
        self.display_single_enable = self.new_bit_attribute(self.ui_in, 6)
        self.input_pulse = self.new_bit_attribute(self.ui_in, 5)
        self.clk_config = self.new_slice_attribute(self.ui_in, 4, 2) # tt.ui_in[4:2]
        # outputs
        self.prox_select = self.new_bit_attribute(self.uo_out, 7)
        self.segments = self.new_slice_attribute(self.uo_out, 6, 0) # tt.uo_out[6:0]
        

def main(serial_port='/dev/ttyACM0'):
    logging.basicConfig(level=logging.DEBUG)
    dut = NeptuneDUT(serial_port)
    dut.write_test_vcds_to_dir = '/tmp'
    neptune_tb.main(dut)
    
if __name__ == '__main__':
    main()
