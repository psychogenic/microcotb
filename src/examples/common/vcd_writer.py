'''
Created on Dec 2, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.time.value import TimeValue
import microcotb.log as logging

log = logging.getLogger(__name__)
class Event:
    VariablesWithEvents = dict()
    @classmethod 
    def reset_known_variables(cls):
        cls.VariablesWithEvents = dict()
        
    @classmethod 
    def variables_with_events(cls):
        return list(cls.VariablesWithEvents.keys())
        
    def __init__(self, ts:TimeValue, var_name:str, new_value:int):
        self.ts = ts 
        self.var_name = var_name
        self.value = new_value
        self.VariablesWithEvents[var_name] = True
        
    def __repr__(self):
        return f'<Event @ {self.ts}: {self.var_name} = {self.value}>'

class VCD:
    WriterClass = None 
    
    @classmethod 
    def writer_class(cls):
        if cls.WriterClass is not None:
            return cls.WriterClass
        try:
            from vcd import VCDWriter
            cls.WriterClass = VCDWriter
        except:
            log.info(f"No VCD support")
            cls.WriterClass = False
            
        return cls.WriterClass
        
    @classmethod 
    def write_supported(cls):
        w_class = cls.writer_class()
        if w_class is None or not w_class:
            return False
        return True
    
    def __init__(self, events_list:list, timescale='1 ns'):
        self.events = events_list
        self.timescale = timescale
        self._known_variables = dict()
        self._variable_settings = dict()
        self._last_values = dict()
        
    
    
    
        
    def add_variable(self, name:str, width:int, scope:str='dut'):
        self._variable_settings[name] = (scope, name, 'wire', width)
        
    def write_to(self, outfile_path:str):
        if not self.write_supported():
            log.error("No VCD write support")
            return False 
        
        log.info(f"Write VCD file to {outfile_path} with {len(self.events)} events")
        
        w_class = self.writer_class()
        outfile = open(outfile_path, 'w')
        with w_class(outfile, timescale=self.timescale, date='today') as writer:
            for vname,settings in self._variable_settings.items():
                self._known_variables[vname] = writer.register_var(*settings, init=0)
                self._last_values[vname] = None
                log.debug(f'Registering variable "{vname}" for VCD')
            
            for evt in self.events:
                event:Event = evt
                if event.var_name not in self._known_variables:
                    raise ValueError(f'{event} has undeclared variable. add it')
                if self._last_values[event.var_name] is not None \
                   and self._last_values[event.var_name] == event.value:
                    # skip it
                    continue
                self._last_values[event.var_name] = event.value
                writer.change(self._known_variables[event.var_name], 
                              int(event.ts.time), event.value)
                
            writer.close()
        outfile.close()
                