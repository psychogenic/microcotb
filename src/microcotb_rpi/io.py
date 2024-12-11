'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.monitorable.io import IO, MonitorableIO
from microcotb.dut import SliceWrapper
from microcotb.types.ioport import DefaultDebounceUSecs
import microcotb.log as logging
log = logging.getLogger(__name__)

try:
    import gpiod
    from gpiod.line import Direction, Value, Edge
    from gpiod.edge_event import EdgeEvent

except ModuleNotFoundError as e:
    log.critical("No 'gpiod' module on this platform--this isn't going to workout smashingly\n\n")
    raise e
    
import datetime 
 


class ConfigurableDirectionIO(IO):
    
    def oe_value_change(self, oe:IO, current_value:int, new_value:int):
        pass


class RPiIO(MonitorableIO):
    
    EdgeEvent = EdgeEvent
    EventType = EdgeEvent.Type
    DefaultEventWaitTimeDelta = datetime.timedelta(microseconds=DefaultDebounceUSecs+1)
    def __init__(self, name:str, pin_list:list, chipname:str="/dev/gpiochip0"):
        width = len(pin_list)
        super().__init__(name, width, self._get_line_values, self._set_line_values)
        
        self.oe = RPiOE(name, width, self)
        oe_value = self.oe.value
        
        # I'm getting really bouncy lines
        # so far, testing shows debounceUSecs 0, but 
        # in one set of tests I needed a 
        # resilientDebounceTries 3 or 4 to be good...
        # but it works with 0 now? wtf? well, can't complain
        self.port.debounceUSecs = 0 
        self.port.resilientDebounceTries = 0
        
        self._chipname = chipname
        self._pin_ids = pin_list
        self._config = dict()
        self._lineoffset_to_bitpos = {}
        
        for i in range(width):
            self._config[self._pin_ids[i]] = self._get_line_settings_config(int(oe_value[i]))
            self._lineoffset_to_bitpos[self._pin_ids[i]] = i
            
        self._line_request = gpiod.request_lines(self._chipname, consumer='microcotb', 
                                                 config=self._config)
        
        
        
    
    @property
    def has_inputs(self):
        #if self.width < 2 and self.oe.value < 1:
        #    return True 
        return self.oe.current_value() < self.oe.max_value
    
    def has_events(self, timeout=DefaultEventWaitTimeDelta):
        if self._line_request.wait_edge_events(timeout):
            evts = self._line_request.read_edge_events()
            return len(evts)
            # print(f'NUM EVENTS! {num}')
            v = self.last_value
            max_val = self.max_value
            #print(f'Events!  last val {v}...', end='')
            data = []
            for ev in evts:
                data.append((ev.global_seqno, ev.timestamp_ns, ev.event_type, bin(ev.line_seqno), self._lineoffset_to_bitpos[ev.line_offset]))
                mask = (1 << self._lineoffset_to_bitpos[ev.line_offset])
                if ev.event_type == EdgeEvent.Type.FALLING_EDGE:
                    v &= (max_val & ~mask) # clear bit
                elif ev.event_type == EdgeEvent.Type.RISING_EDGE:
                    v |= mask # set bit
            
            #print(f'now set to {v}')
            print('\n\t'.join(list(map(lambda x: str(x), data))))
            self.port.do_force_update_last_value(v)
            return evts
        return None
    
    @property 
    def line_request(self) -> gpiod.LineRequest:
        return self._line_request
    
    def _get_line_settings_config(self, for_output:bool) -> gpiod.LineSettings:
        if for_output:
            return gpiod.LineSettings(
                            direction=Direction.OUTPUT, output_value=Value.ACTIVE
                        )
        
        return gpiod.LineSettings(
                            direction=Direction.INPUT, edge_detection=Edge.BOTH,
                            debounce_period=datetime.timedelta(microseconds=self.port.debounceUSecs))
        
    def _get_line_values(self):
        v = 0
        for bitV in reversed(self.line_request.get_values(self._pin_ids)):
            v = v * 2 + bitV.value # Supposedly faster than shifting
        return v
    
    def _set_line_values(self, set_to:int):
        
        oe_value = self.oe.value
        set_val_conf = dict()
        for i in range(len(oe_value)):    
            if oe_value[i] == True:
                set_val_conf[self._pin_ids[i]] =  Value.ACTIVE if (set_to & (1 << i)) else Value.INACTIVE
        
        if len(set_val_conf):
            self.line_request.set_values(set_val_conf)
                
    @property 
    def pin_ids(self):
        return self._pin_ids
    
    def oe_value_change(self, oe:IO, current_value:int, new_value:int):
        changed = current_value ^ new_value
        if not changed:
            return
        new_config = dict()
        for i in range(self.port.width):
            if changed & (1 << i):
                new_settings = self._get_line_settings_config(new_value & (1 << i) )
                new_config[self._pin_ids[i]] = new_settings
            else:
                new_config[self._pin_ids[i]] = self._config[self._pin_ids[i]]
        
        self.line_request.reconfigure_lines(new_config)
        
    
    def __setattr__(self, name:str, value):
        # these are special ports in that they have OE attributes
        # that are ports themselves... allow for the same 
        # convenince of doing port.oe = XX to set the sub-port value
        if hasattr(self, name):
            port = getattr(self, name)
            if isinstance(port, (IO, SliceWrapper)):
                port.value = value 
                return
        
        super().__setattr__(name, value)

class RPiOE(IO):
    def __init__(self, name:str, width:int, managed_io:ConfigurableDirectionIO):
        super().__init__(f'{name}_oe', width, self.current_value, self.set_current_value)
        self._managed_name = name
        self._current_value = 0
        self._managed_io = managed_io
        self._write_notif_callback = None 
        
    def managed_port_name(self):
        return self._managed_name
        
    def current_value(self) -> int:
        return self._current_value
    
    def set_current_value(self, set_to:int):
        old_val = self._current_value
        self._current_value = set_to 
        self._managed_io.oe_value_change(self, old_val, set_to)
        
             
                
