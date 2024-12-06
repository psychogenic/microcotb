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
        if not hasattr(self, 'ui_in'):
            raise RuntimeError('Does not look like a TT DUT')
        self.add_bit_attribute('display_single_select',
                                    self.ui_in, 7)
        self.add_bit_attribute('display_single_enable',
                                    self.ui_in, 6)
        self.add_bit_attribute('input_pulse', 
                                    self.ui_in, 5)
        # tt.ui_in[4:2]
        self.add_slice_attribute('clk_config', 
                                    self.ui_in, 4, 2) 
        # outputs
        self.add_bit_attribute('prox_select', self.uo_out, 7)
        # tt.uo_out[6:0]
        self.add_slice_attribute('segments', self.uo_out, 6, 0) 


def main(serial_port='/dev/ttyACM0'):
    logging.basicConfig(level=logging.DEBUG)
    dut = NeptuneDUT(serial_port)
    # dut.write_test_vcds_to_dir = '/tmp'
    neptune_tb.main(dut)
    
if __name__ == '__main__':
    main()
