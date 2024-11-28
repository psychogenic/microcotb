'''
Created on Nov 28, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import time
import serial
DefaultPort = '/dev/ttyACM0'

import microcotb.log as logging
import microcotb.dut 

log = logging.getLogger(__name__)

# 0bINAAAAVR
# I == 0: command, I==1 IO
# N == 1: multi-bit io
# 0AAAA: single bit IO address, 4 bits, 16 quick singles
# 1AAAAV: multi-bit IO address, 5 bits, 32 multi-bit
# V: value for single bit write, when R==0
class Signal:
    def __init__(self, serial_port, name, addr):
        self.name = name
        self.address = addr
        self.multi_bit = addr & 32
        self._current_value = None
        self._serport = serial_port
        
    @property 
    def value(self):
        return self.read()
    
    @value.setter 
    def value(self, set_to:int):
        self.write(set_to)
        
        
    def toggle(self):
        if self.multi_bit:
            raise RuntimeError('Cannot toggle multi-bits')
        if self._current_value:
            self.write(0)
        else:
            self.write(1)
            
    def clock(self):
        self.toggle()
        self.toggle()

    def read(self):
        cmd = 1<<7 # io rw
        if self.multi_bit:
            cmd |= self.address << 1
        else:
            cmd |= self.address << 2
            
        cmd |= 1 # is a read
        
        # print(f"READ {bin(cmd)}")
        ser = self._serport
        ser.write(bytearray([cmd]))
        time.sleep(0.05)
        v = ser.read()
        if len(v):
            self._current_value = int.from_bytes(v, 'big')
            
        return self._current_value
    
    
    def write(self, val:int):
        cmd = 1<<7 # io rw
        if self.multi_bit:
            cmd |= self.address << 1
            send_bytes = bytearray([cmd, val])
        else:
            cmd |= self.address << 2
            if val:
                cmd |= 1<<1
            send_bytes = bytearray([cmd])

        self._current_value = val
        ser = self._serport
        ser.write(send_bytes)

class DUT(microcotb.dut.DUT):
    def __init__(self, serial_port:str=DefaultPort):
        super().__init__('SUB')
        self.port = serial_port 
        self._serial = None 
        
    @property 
    def serial(self):
        if self._serial is None:
            self._serial = serial.Serial(self.port, 115200, timeout=0.5)
            
        return self._serial

    def add_signal(self, name, addr):
        setattr(self, name, Signal(self.serial, name, addr))
        
    
    def testing_will_begin(self):
        self.discover()
        
        
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
                addr = int.from_bytes(kv[1], "big")
                log.info(f'Have signal {nm} at {addr}')
                self.add_signal(nm, addr)

        


