'''
Created on Nov 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import time

class Signal:
    '''
        A signal we can read and perhaps write to through the 
        bridge.
        Always requires sending at least 1 byte, the command 
        byte, with format
        # 0bINAAAAVR
        # I == 0: command, I==1 IO
        # N == 1: multi-bit io
        # 0AAAA: single bit IO address, 4 bits, 16 quick singles
        # 1AAAAV: multi-bit IO address, 5 bits, 32 multi-bit
        # V: value for single bit write, when R==0
    '''
    def __init__(self, serial_port:serial.Serial, 
                 name:str, 
                 addr:int,
                 width:int,
                 is_writeable:bool):
        self.name = name
        self.address = addr
        self.width = width
        self.multi_bit = addr & 32
        self._current_value = None
        self._serport = serial_port
        self._written_to = False
        self._writeable = is_writeable
        self._base_writecmd = None
        self._base_readcmd = None
        
    def reset(self):
        self._written_to = False
        
    @property 
    def serial(self) -> serial.Serial:
        return self._serport
    
    @property
    def is_writeable(self) -> bool:
        return self._writeable
    
    @property 
    def value(self):
        return self.read()
    
    @value.setter 
    def value(self, set_to:int):
        self.write(set_to)
        
        
    def toggle(self):
        if self.width > 1:
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
        if self._base_readcmd is None:
            cmd = 1<<7 # io rw
            if self.multi_bit:
                cmd |= self.address << 1
            else:
                cmd |= self.address << 2
                
            cmd |= 1 # is a read
            self._base_readcmd = cmd
        
        self.serial.write(bytearray([self._base_readcmd]))
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
        if self._base_writecmd is None:
            cmd = 1<<7 # io rw
            if self.multi_bit:
                cmd |= self.address << 1
            else:
                cmd |= self.address << 2
            self._base_writecmd = cmd
        
        if self.multi_bit:
            send_bytes = bytearray([self._base_writecmd, val])
        else:
            cmd = self._base_writecmd
            if val:
                cmd |= 1<<1
            send_bytes = bytearray([cmd])

        self._current_value = val
        if self.serial.out_waiting:
            self.serial.flushOutput()
        self.serial.write(send_bytes)
        
        
    def __repr__(self):
        return f'<Signal {self.name}>'
