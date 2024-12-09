'''
Created on Dec 8, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb_rpi.dut import DUT, StateChangeReport

class SimpleIO(DUT):
    def __init__(self, name:str='SimpleIO', 
                 state_change_callback=None,
                 configurable_port_suffix:str='_oe'):
        super().__init__(name, state_change_callback, configurable_port_suffix)
        self.always_queue_reports = False
        
    
    # override
    def append_state_change(self, stch:StateChangeReport):
        # this override is here to ensure we don't just
        # spend our time storing state changes in mem
        # for a user who's not caring about VCDs and 
        # won't flush them out.
        if self.write_vcd_enabled or self.always_queue_reports:
            super().append_state_change(stch)
        else:
            # we are responsible for subfields in there
            self.add_subfields_to_report(stch)
        self.trigger_all_state_callbacks(stch)
            