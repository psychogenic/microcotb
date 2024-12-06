'''
Created on Nov 29, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import time
import serial
import microcotb.log as logging

log = logging.getLogger(__name__)

AsynchronousStateNotifs = True
PollShortDelay = 0.002
PollCertainDelay = 0.005


SuperVerbose = False
def verbose_debug(msg):
    if SuperVerbose:
        log.warning(msg)
        
        
class Signal:
    '''
        A signal we can read and perhaps write to through the 
        bridge.
    '''
    def __init__(self, 
                 name:str, 
                 addr:int,
                 width:int,
                 is_writeable:bool):
        self.name = name
        self.address = addr
        self.width = width
        self.multi_bit = addr & 32
        self._current_value = None
        self._written_to = False
        self._writeable = is_writeable
        self._base_writecmd = None
        self._base_readcmd = None
        
    def reset(self):
        self._written_to = False
        
    
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

        
    def __repr__(self):
        return f'<Signal {self.name}>'


class SerialStream:
    def __init__(self, serport:serial.Serial):
        self.serial = serport
        try:
            self.serial.set_low_latency_mode(True)
        except:
            log.error("Could not set low_latency_mode")
        self.reading_state_changes = False 
        self.stream = bytearray()
        self.state_stream = bytearray()
        self.state_byte = 0
        self.suspend_state_monitoring = False
        
    def get_stream(self):
        if not len(self.stream):
            return self.stream
        s = self.stream 
        self.stream = bytearray()
        return s
    
    def get_state_stream(self):
        if not len(self.state_stream):
            return self.state_stream
        
        s = self.state_stream
        self.state_stream = bytearray()
        return s
    @property 
    def state_stream_size(self) -> int:
        return len(self.state_stream)
    
    @property 
    def stream_size(self) -> int:
        return len(self.stream)
    
    def write_out(self, bts:bytearray):
        verbose_debug(f'writeout {bts}')
        while self.serial.out_waiting:
            time.sleep(0.001)
        return self.serial.write(bts)
    
    def poll(self, size=None, delay:float = 0, wait_for_atleast:int=0):
        
        if delay > 0:
            time.sleep(delay)
            
        if wait_for_atleast:
            while self.serial.in_waiting < wait_for_atleast:
                time.sleep(0.001)
                
        if size is not None:
            self.stream += self.serial.read(size)
            verbose_debug(f"poll {size}, stream now {self.stream}")
            return
        
        if self.suspend_state_monitoring:
            while self.serial.in_waiting:
                self.stream += self.serial.read_all()
            verbose_debug(f"susp state mon poll, stream now {self.stream}")
            return
        
        # verbose_debug(f"regular poll (size {size})")
        
        while self.serial.in_waiting or self.reading_state_changes:
            
            v = self.serial.read()
            if not len(v):
                if not self.reading_state_changes:
                    raise RuntimeError('empty v from ser read??')
            val = v[0]
            
            
            if not self.reading_state_changes:
                
                if val == ord('m'):
                    verbose_debug(f"not stat chng, but got 'm'")
                    self.state_stream += v
                    self.reading_state_changes = True
                    self.state_byte = 0
                    while not self.serial.in_waiting:
                        time.sleep(PollShortDelay)
                else:
                    verbose_debug(f"not stat chng got {v}")
                    self.stream += v
            else:
                if self.state_byte == 0 and val == 0xff:
                    verbose_debug(f"stat chng got eof")
                    self.state_stream += v
                    self.reading_state_changes = False
                elif self.state_byte == 0 and val == ord('m'):
                    verbose_debug(f"stat chng got 'm'")
                    # another m
                    self.state_stream += v
                    while not self.serial.in_waiting:
                        time.sleep(PollShortDelay)
                else:
                    verbose_debug(f"stat chng got {v} now at {self.state_byte} byte")
                    
                    if self.state_byte == 0:
                        # multibits have address 1AAAAV
                        # singlebits have address 0AAAA
                        address = val & 0b111111
                        if address <= 0b1111:
                            # single bit, value is stashed in high bit
                            bit_value = 1 if val & 0x80 else 0
                            self.state_stream += bytearray([address, bit_value])
                            self.state_byte = 0
                        else:
                            self.state_stream += bytearray([address])
                            self.state_byte += 1
                    else:
                        self.state_stream += v
                        self.state_byte += 1
                        
                    if self.state_byte >= 2:
                        self.state_byte = 0
                    #if not self.serial.in_waiting:
                    #    time.sleep(PollShortDelay)







class SUBSignal(Signal):
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
    def __init__(self, serial_stream:SerialStream, 
                 name:str, 
                 addr:int,
                 width:int,
                 is_writeable:bool):
        super().__init__(name, addr, width, is_writeable)
        self._serstream = serial_stream
        # self._serport = serial_port
        
    @property 
    def serial_stream(self) -> SerialStream:
        return self._serstream

    def read(self):
        if self._base_readcmd is None:
            cmd = 1<<7 # io rw
            if self.multi_bit:
                cmd |= self.address << 1
            else:
                cmd |= self.address << 2
                
            cmd |= 1 # is a read
            self._base_readcmd = cmd
        
        sus = self.serial_stream.suspend_state_monitoring
        delay = 0
        if AsynchronousStateNotifs and not sus:
            delay=PollCertainDelay # monitoring, need to slow it down to ensure we get only our value back
        self.serial_stream.poll(delay=delay)
        self.serial_stream.suspend_state_monitoring = True
        self.serial_stream.write_out(bytearray([self._base_readcmd]))
        
        self.serial_stream.poll(1)
        v = self.serial_stream.get_stream()
        if len(v):
            self._current_value = int.from_bytes(v, 'big')
            
        self.serial_stream.suspend_state_monitoring = sus 
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
        while self.serial_stream.serial.out_waiting:
            time.sleep(0.001)
            
        
        self.serial_stream.poll()
        sus = self.serial_stream.suspend_state_monitoring
        self.serial_stream.suspend_state_monitoring = True
        self.serial_stream.write_out(send_bytes)
        self.serial_stream.suspend_state_monitoring = sus
        self.serial_stream.poll()
        
    def __repr__(self):
        return f'<SUBSignal {self.name}>'
