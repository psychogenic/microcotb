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
    def __init__(self, serial_port:serial.Serial, name:str, addr:int):
        self.name = name
        self.address = addr
        self.multi_bit = addr & 32
        self._current_value = None
        self._serport = serial_port
        self._written_to = False
        
    def reset(self):
        self._written_to = False
        
    @property 
    def serial(self) -> serial.Serial:
        return self._serport
    
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
            
    def clock(self, num_times:int = 1):
        for _i in range(num_times):
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
        
        self.serial.write(bytearray([cmd]))
        while not self.serial.in_waiting:
            time.sleep(0.001)
        v = self.serial.read()
        if len(v):
            self._current_value = int.from_bytes(v, 'big')
            
        return self._current_value
    
    
    def write(self, val:int):
        if self._written_to and val == self._current_value:
            return 
        
        self._written_to = True
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
        if self.serial.out_waiting:
            self.serial.flushOutput()
        self.serial.write(send_bytes)

class DUT(microcotb.dut.DUT):
    def __init__(self, serial_port:str=DefaultPort, name:str='SUB'):
        super().__init__(name)
        self.port = serial_port 
        self._serial = None 
        self._added_signals = []
        
    @property 
    def serial(self) -> serial.Serial:
        if self._serial is None:
            self._serial = serial.Serial(self.port, 115200, timeout=0.5)
        return self._serial

    def add_signal(self, name, addr):
        s = Signal(self.serial, name, addr)
        self._added_signals.append(s)
        setattr(self, name, s)
        
    
    def testing_will_begin(self):
        self.discover()
        
    
    def testing_unit_done(self, test:microcotb.dut.TestCase):
        for s in self._added_signals:
            s.reset()
        
        
    def dump_state(self):
        ser = self.serial 
        ser.write(b'd')
        time.sleep(1)
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
                addr = int.from_bytes(kv[1], "big")
                log.info(f'Have signal {nm} at {addr}')
                self.add_signal(nm, addr)


def getDUT(port:str='/dev/ttyACM0'):
    dut = DUT(port)
    dut.discover()
    return dut

