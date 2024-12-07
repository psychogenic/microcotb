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
import examples.common.shaman_tb

import examples.fpga_io.tt_dut as tt_dut

class ShamanDUT(tt_dut.TinyTapeoutDUT):
    '''
        Rather than setup neptune-specific signal mappings on the FPGA,
        doing it here allows a single I/O-through SUB FPGA to work with 
        *any* tiny tapeout project.
        
        So the base class DUT will expose ui_in, uo_out etc for all projects,
        and here we create named attributes using bits and slices from those
        standard signals, that are used in the testbench.
    '''
    def __init__(self, serial_port:str):
        super().__init__(serial_port, 'SHAMAN', auto_discover=True)

        self.databyteIn = self.ui_in
        self.resultbyteOut = self.uo_out
        
        self.resultReady = self.new_bit_attribute('resultReady', self.uio_out, 0)
        self.beginProcessingDataBlock = self.new_bit_attribute('beginProcessingDataBlock', self.uio_out, 1)
        
        self.parallelLoading = self.new_bit_attribute('parallelLoading', self.uio_in, 2)
        self.resultNext = self.new_bit_attribute('resultNext', self.uio_in, 3)
        
        self.busy = self.new_bit_attribute('busy', self.uio_out, 4)
        self.processingReceivedDataBlock = self.new_bit_attribute('processingReceivedDataBlock', self.uio_out, 5)
        self.start = self.new_bit_attribute('start', self.uio_in, 6)
        self.clockinData = self.new_bit_attribute('clockinData', self.uio_in, 7)
        
        self.oe_bidir_setting = 0b11001100
        


import logging
def main(ser_port:str='/dev/ttyACM0'):
    from microcotb.time.value import TimeValue
    TimeValue.ReBaseStringUnits = True # want pretty strings

    logging.basicConfig(level=logging.INFO)
    
    dut = ShamanDUT(ser_port)
    dut.is_monitoring = True
    dut.sync_change_dumps =  True
    
    dut.uio_oe.value = dut.oe_bidir_setting
    
    runner = cocotb.get_runner(__name__)
    dut._log.info(f"enabled shaman project. Will test with\n{runner}")
    runner.test(dut)

if __name__ == '__main__':
    main()