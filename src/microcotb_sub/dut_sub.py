'''
Created on Nov 28, 2024

This is a basic implementation for the simple USB bridge protocol, 
going over USB serial to talk to a DUT.

It's developped in conjunction with my FPGA-side, so is strictly 
bound to that specific protocol.

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import time
import serial

DefaultPort = '/dev/ttyACM0'

import microcotb.log as logging
from microcotb_sub.signal import SUBSignal, SerialStream
from microcotb_sub.dut import DUT as BaseDUT
from microcotb_sub.dut import StateChangeReport, SUBIO


            

class SUBStateChangeReport(StateChangeReport):
    LeftOvers = None
    def __init__(self, report:bytearray=b'', io_by_address:dict=None):
        super().__init__()
        if len(report) and io_by_address is not None:
            self.parse_report(report, io_by_address)
        
    def parse_report(self, report:bytearray, io_by_address:dict):
        # print(report)
        if self.LeftOvers is not None:
            report = self.LeftOvers + report 
            print(f'REP+LFT{report}')
            self.LeftOvers = None
            
        i = 0
        while i < len(report):
            
            while (report[i] == 0xff) or (report[i] == ord('m')):
                # skip over start and any EOF
                i += 1
                if i >= len(report):
                    # print(f"EVN {len(self)}")
                    return
            
            if len(report) >= i+2:
                port_addr = report[i]
                if port_addr in io_by_address:
                    pname = io_by_address[port_addr].port.name
                    pvalue = report[i+1]
                    self.add_change(pname, pvalue)
                else:
                    raise Exception(f"AAAAAGHZ {port_addr}")
                i += 2
            else:
                self.LeftOvers = report[i:]
                # print(f"LFTVR: {report[i:]} self:{len(self)}")
                return

class DUT(BaseDUT):
    def __init__(self, serial_port:str=DefaultPort, 
                 name:str='SUB', 
                 auto_discover:bool=False):
        
        self.port = serial_port
        self.asynchronous_events = True
        self._serial = None
        self._stream = None
        super().__init__(name, auto_discover)
    
    @property 
    def ser_stream(self) -> SerialStream:
        if self._stream is None:
            self._stream = SerialStream(serial.Serial(self.port, 115200*6, timeout=0.5))
        return self._stream
    @property 
    def serial(self) -> serial.Serial:
        ser = self.ser_stream.serial
        if not ser.is_open:
            raise RuntimeError(f'Serial {self.port} is not open?')
        return ser

        
    def add_signal(self, name, addr, width:int, is_writeable_input:bool=False):
        s = SUBSignal(self.ser_stream, name, addr, width, is_writeable_input)
        self._added_signals[name] = s
        if width is None:
            # take a guess
            if s.multi_bit:
                self._log.warning(f'GUESSING that {name} is 8 bits wide!')
                width = 8
            else:
                self._log.warning(f'GUESSING that {name} is 1 bit wide!')
                width = 1
            
        def reader():
            if self.is_monitoring:
                if self.asynchronous_events:
                    self.poll_statechanges()
                if self.state_cache.has(name):
                    return self.state_cache.get(name)
                
            return s.read()
        
        def writer(v:int):
            if self.is_monitoring:
                # make note of what we've done
                if self.asynchronous_events:
                    self.poll_statechanges()
                chg = StateChangeReport()
                alias_name = self.aliased_name_for(name)
                chg.add_change(alias_name, v)
                self.append_state_change(chg)
                self.state_cache.set(alias_name, v)
                    
            # print('W', end='')
            s.write(v)
            if self.is_monitoring:
                if self.asynchronous_events:
                    time.sleep(0.0015) # TODO:FIXME sleep
                    while self.serial.out_waiting:
                        time.sleep(0.001) # TODO:FIXME sleep
                self.poll_statechanges()
        
        wrt = None
        if s.is_writeable:
            wrt = writer 
            
        iop = SUBIO(s, name, width, reader, wrt)
        setattr(self, name, iop)
        self._signal_by_address[s.address] = iop
        
    
    def testing_unit_start(self, test):
        self.poll_general(delay=0.05) # make sure we flush anything
        super().testing_unit_start(test)
        
    def testing_unit_done(self, test):
        super().testing_unit_done(test)
        self.poll_general(delay=0.05)
        if self.ser_stream.stream_size:
            self._log.error("TEST UNIT DONE: STREAM HAS")
            self._log.error(self.ser_stream.get_stream())
        
        
    @property 
    def is_monitoring(self):
        return self._is_monitoring
    
    @is_monitoring.setter
    def is_monitoring(self, set_to:bool):
        old_state = self._is_monitoring
        if set_to:
            self._is_monitoring = True
            bts = bytearray([ord('m'), 1])
        else:
            self._is_monitoring = False
            bts = bytearray([ord('m'), 0])
        
        if self._is_monitoring and not old_state:
            for stch in self.vcd_initial_state_reports():
                self.append_state_change(stch)
            
        
        return self.send_and_recv_command(bts, 100)
    
    @property 
    def sync_change_dumps(self):
        return self._use_sync_cd
    
    @sync_change_dumps.setter
    def sync_change_dumps(self, set_to:bool):
        if set_to:
            self.is_monitoring = True
            self._use_sync_cd = True
            bts = b's\x01'
        else:
            self._use_sync_cd = False
            bts = b's\x00'
        return self.send_and_recv_command(bts, 100)
    
    def send_and_recv_command(self, cmd:bytearray, max_size:int=500, delay:float=None):
        # print(f"SNR {cmd} {max_size}")
        if self.asynchronous_events:
            self.poll_statechanges()
        self.ser_stream.suspend_state_monitoring = True
        self.poll_general()
        self.ser_stream.write_out(cmd)
        if delay is None:
            delay=0.05
        self.poll_general(max_size, delay=delay)
        a = self.ser_stream.get_stream()
        self.ser_stream.suspend_state_monitoring = not self.is_monitoring
        return a
        
        
    def dump_state(self):
        
        a = self.send_and_recv_command(b'd', 1000)
        try:
            print(a.decode())
        except:
            pass
        return a
        
    def discover(self):
        self._log.info('SUB DUT performing discovery')
        ser = self.serial 
        if not ser:
            raise RuntimeError(f'Could not get a serial port on {self.port}')
        if not ser.is_open:
            raise RuntimeError(f'Serial port on {self.port} not open')

        a = self.send_and_recv_command(b'l', 2000, delay=0.2)
        fields = a.split(b'|')
        # print(fields)
        discovered_fields = []
        for f in fields:
            if not len(f):
                continue
            kv = f.split(b'~')
            if len(kv) > 1:
                nm = kv[0].decode()
                if len(kv[1]) < 2:
                    self._log.error(f"field {nm} has insufficient values in listing {kv}")
                    continue
                
                if len(kv[1]) > 2:
                    self._log.warning(f"field {nm} has more bytes than expected in listing {kv[1]}")
                    
                addr = kv[1][0]
                desc = kv[1][1]
                is_input = True if desc & (1<<7) else False 
                width = desc & 0x7f
                self._log.debug(f'Have signal {nm} ({width}) at {addr} (from {kv[1]}) (input: {is_input})')
                self.add_signal(nm, addr, width, is_input)
                discovered_fields.append(nm)
                
        
        syncbytes = bytearray([ord('s'), 0 if self.asynchronous_events else 1])
        self.send_and_recv_command(syncbytes, 100)
        
        desc = []
        for df in sorted(discovered_fields):
            field:SUBIO = getattr(self, df)
            r = 'r' if field.is_readable else ''
            w = 'w' if field.is_writeable else '' 
            slc = ''
            if field.width > 1:
                slc = f'[{field.width-1}:0]'
            if r and w:
                rw = f'{r}{w}'
            else:
                rw = f'{r}{w} '
                
            desc.append(f'\t{rw} dut.{field.name}{slc}')
        
        names = '\n'.join(desc)
        self._log.info(f'Discovered fields:\n{names}')

    def poll_general(self, size=None, delay:float=0, suspend_state_stream:bool=False):
        
        oldval = self.ser_stream.suspend_state_monitoring
        self.ser_stream.suspend_state_monitoring = suspend_state_stream
        
        self.ser_stream.poll(size, delay)
        
        
        self.ser_stream.suspend_state_monitoring = oldval
        
        return self.ser_stream.stream_size
        
    def poll_statechanges(self):
        wait_at_least = 0
        if not self.asynchronous_events:
            self.ser_stream.write_out(b'c') # get state change 
            wait_at_least = 2
            
        self.ser_stream.poll(wait_for_atleast=wait_at_least)
        if self.ser_stream.state_stream_size:
            s = SUBStateChangeReport(self.ser_stream.get_state_stream(), self._signal_by_address)
            if len(s):
                self.append_state_change(s)
                self.state_cache.change_event(s)
                 
            return s 
        
        return len(self.queued_state_changes)

    
    def keepPolling(self):
        while True:
            self.poll_statechanges()
            stch = self.get_queued_state_changes()
            for i in stch:
                print(i[1])
            time.sleep(0.05)
            
    
def getDUT(port:str='/dev/ttyACM0', name:str='SUB'):
    logging.basicConfig(level=logging.DEBUG)
    dut = DUT(port, name, auto_discover=True)
    return dut


