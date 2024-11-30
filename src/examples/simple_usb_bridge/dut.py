'''
Created on Nov 28, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import time
import serial

DefaultPort = '/dev/ttyACM0'

from examples.simple_usb_bridge.signal import Signal
from microcotb.ports.io import IO

import microcotb.log as logging
import microcotb.dut 

log = logging.getLogger(__name__)

class SUBIO(IO):
    '''
        Derive from IO, mostly to implement our between-test reset() optimization
    '''
    def __init__(self, sig:Signal, name:str, width:int, read_signal_fn=None, write_signal_fn=None):
        super().__init__(name, width, read_signal_fn, write_signal_fn)
        self._sub_signal = sig
        
    
    def reset(self):
        self._sub_signal.reset()
        
    @property
    def is_writeable(self) -> bool:
        return self._sub_signal.is_writeable
    
    
    def toggle(self):
        if int(self.value):
            self.value = 1
        else:
            self.value = 0
            
    def clock(self, num_times:int = 1):
        for i in range(num_times):
            self.toggle()
            self.toggle()

class DUT(microcotb.dut.DUT):
    def __init__(self, serial_port:str=DefaultPort, name:str='SUB', auto_discover:bool=False):
        super().__init__(name)
        self.port = serial_port 
        self._serial = None 
        self._added_signals = dict()
        self._alias_to_signal = dict()
        
        if auto_discover:
            self.discover()
        
    @property 
    def serial(self) -> serial.Serial:
        if self._serial is None:
            self._serial = serial.Serial(self.port, 115200, timeout=0.5)
            
        if not self._serial.is_open:
            raise RuntimeError(f'Serial {self.port} is not open?')
        return self._serial

    def alias_signal(self, name:str, s:Signal):
        setattr(self, name, s)
        self._added_signals[name] = s
    def add_signal(self, name, addr, width:int, is_writeable_input:bool=False):
        s = Signal(self.serial, name, addr, width, is_writeable_input)
        self._added_signals[name] = s
        
        if width is None:
            # take a guess
            if s.multi_bit:
                width = 8
            else:
                width = 1
                
                
            
        def reader():
            return s.read()
        
        def writer(v:int):
            s.write(v)
        
        wrt = None
        if s.is_writeable:
            wrt = writer 
            
        iop = SUBIO(s, name, width, reader, wrt)
        setattr(self, name, iop)
        
    
    def testing_will_begin(self):
        # use auto-discover instead self.discover()
        super().testing_will_begin()
        
    
    def testing_unit_done(self, test:microcotb.dut.TestCase):
        for s in self._added_signals.values():
            s.reset()
        
        
    def dump_state(self):
        ser = self.serial 
        ser.write(b'd')
        time.sleep(0.06)
        a = ser.read(1000)
        print(a.decode())
        return a
        
    def discover(self):
        log.info('SUB DUT performing discovery')
        ser = self.serial 
        if not ser:
            raise RuntimeError(f'Could not get a serial port on {self.port}')
        if not ser.is_open:
            raise RuntimeError(f'Serial port on {self.port} not open')

        ser.write(b'l')
        time.sleep(1)
        a = ser.read(500)
        fields = a.split(b'\n')
        for f in fields:
            if not len(f):
                continue
            kv = f.split(b':')
            if len(kv) > 1:
                nm = kv[0].decode()
                if len(kv[1]) < 2:
                    log.error(f"field {nm} has insufficient values in listing {kv[1]}")
                    continue
                
                if len(kv[1]) > 2:
                    log.warning(f"field {nm} has more bytes than expected in listing {kv[1]}")
                    
                addr = kv[1][0]
                desc = kv[1][1]
                is_input = True if desc & (1<<7) else False 
                width = desc & 0x7f
                log.error(f'Have signal {nm} ({width}) at {addr} (from {kv[1]}) (input: {is_input})')
                self.add_signal(nm, addr, width, is_input)
                
        
                
    def __setattr__(self, name:str, value):
        if hasattr(self, '_added_signals') and name in self._added_signals \
            and isinstance(value, int):
            self._added_signals[name].value = value
            return 
        
        super().__setattr__(name, value)
            
        


def getDUT(port:str='/dev/ttyACM0', name:str='SUB'):
    dut = DUT(port, name, auto_discover=True)
    return dut


