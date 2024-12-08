'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
'''
Created on Dec 7, 2024

All the tests themselves are in examples.common, this is just
specifics about how we're running

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import microcotb as cocotb


cocotb.set_runner_scope(__name__)
# get the @cocotb.test()s loaded
import examples.common.neptune_tb

import examples.raspi.tt_dut as rpidut


class NeptuneDUT(rpidut.TinyTapeoutDUT):
    '''
        Rather than setup neptune-specific signal mappings on the FPGA,
        doing it here allows a single I/O-through SUB FPGA to work with 
        *any* tiny tapeout project.
        
        So the base class DUT will expose ui_in, uo_out etc for all projects,
        and here we create named attributes using bits and slices from those
        standard signals, that are used in the testbench.
    '''
    def __init__(self):
        super().__init__('Neptune')
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

from microcotb.time.value import TimeValue
import microcotb.log as logging
def main(dut:NeptuneDUT = None):
    TimeValue.ReBaseStringUnits = True
    logging.basicConfig(level=logging.DEBUG)
    runner = cocotb.get_runner(__name__)
    if dut is None:
        dut = NeptuneDUT()
    dut._log.info(f"enabled neptune project, will test with {runner}")
    
    # enable saving VCDs
    dut.is_monitoring = True
    dut.write_vcd_enabled = True
    dut.write_test_vcds_to_dir = '/tmp'
    
    runner.test(dut)

if __name__ == '__main__':
    main()