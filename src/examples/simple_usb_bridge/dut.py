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


class DUT(microcotb.dut.DUT):
    def __init__(self, serial_port:str=DefaultPort, name:str='SUB', auto_discover:bool=False):
        super().__init__(name)
        self.port = serial_port 
        self._serial = None 
        self._added_signals = []
        if auto_discover:
            self.discover()
        
    @property 
    def serial(self) -> serial.Serial:
        if self._serial is None:
            self._serial = serial.Serial(self.port, 115200, timeout=0.5)
        return self._serial

    def add_signal(self, name, addr, width:int, is_writeable_input:bool=False):
        s = Signal(self.serial, name, addr, width, is_writeable_input)
        self._added_signals.append(s)
        
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
            
        iop = IO(name, width, reader, wrt)
        setattr(self, name, iop)
        
    
    def testing_will_begin(self):
        self.discover()
        
    
    def testing_unit_done(self, test:microcotb.dut.TestCase):
        for s in self._added_signals:
            s.reset()
        
        
    def dump_state(self):
        ser = self.serial 
        ser.write(b'd')
        time.sleep(0.05)
        a = ser.read(500)
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
                log.info(f'Have signal {nm} ({width}) at {addr} (from {kv[1]}) (input: {is_input})')
                self.add_signal(nm, addr, width, is_input)


def getDUT(port:str='/dev/ttyACM0', name:str='SUB'):
    dut = DUT(port, name, auto_discover=True)
    return dut


