'''
Created on Nov 28, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
import time
import serial
import os

DefaultPort = '/dev/ttyACM0'

from examples.simple_usb_bridge.signal import Signal
from microcotb.ports.io import IO

import microcotb.log as logging
import microcotb.dut 
from microcotb.time.system import SystemTime
from examples.simple_usb_bridge.vcd_writer import Event, VCD

log = logging.getLogger(__name__)


class StateChangeReport:
    LeftOvers = None
    def __init__(self, report:bytearray=b'', io_by_address:dict=None):
        self._changed_ports = dict()
        self._num_changes = 0
        if len(report) and io_by_address is not None:
            self.parse_report(report, io_by_address)
        
    def parse_report(self, report:bytearray, io_by_address:dict):
        
        i = 1
        # print(report)
        if self.LeftOvers is not None:
            report = self.LeftOvers + report 
            self.LeftOvers = None
        while i < len(report):
            
            while (report[i] == 0xff) or (report[i] == ord('m')):
                i += 1
                if i >= len(report):
                    return
            
            
            if len(report) >= i+3:
                port_addr = report[i]
                if port_addr in io_by_address and report[i+1] == ord('='):
                    pname = io_by_address[port_addr].port.name
                    pvalue = report[i+2]
                    self.add_change(pname, pvalue)
                else:
                    print(f'{port_addr} in io_by_address and {report[i+1]} == {ord("=")}?')
                i += 3
            elif report[i] == 0xff:
                print(f"got ff: {report[i:]}")
                i += 1
            elif report[i] == ord('m'):
                print("got m")
                i += 1
            else:
                print(f"WEIRD: \n{report}\n{report[i:]}")
                return
        
    def add_change(self, pname:str, pvalue:int):
        self._changed_ports[pname] = pvalue
        setattr(self, pname, pvalue)
        self._num_changes += 1
    def changed(self):
        return list(self._changed_ports.keys())     
    def all_changes(self):
        return list(self._changed_ports.items())
    def __len__(self):
        return len(self._changed_ports)
    def __repr__(self):
        return f'<StateChangeReport with {len(self._changed_ports)} (in {self._num_changes}) changes>'
    
    def __str__(self):
        outlist = []
        for k,v in self._changed_ports.items():
            outlist.append(f'{k} = {hex(v)}')
        if not len(outlist):
            return 'StateChangeReport: no changes'
        sep = '\n'
        return f"StateChangeReport ({len(outlist)} ports in {self._num_changes} events):\n{sep.join(outlist)}"
            
  

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
        for _i in range(num_times):
            self.toggle()
            self.toggle()

class DUT(microcotb.dut.DUT):
    def __init__(self, serial_port:str=DefaultPort, 
                 name:str='SUB', 
                 auto_discover:bool=False):
        super().__init__(name)
        self.port = serial_port
        self.write_test_vcds_to_dir = None
        self._serial = None 
        self._added_signals = dict()
        self._signal_by_address = dict()
        self._alias_to_signal = dict()
        self._is_monitoring = False
        self._queued_state_changes = []
        self._signal_name_to_alias = None
        self.events_of_interest_per_test = dict()
        
        if auto_discover:
            self.discover()
            
    def poll(self, return_state_reports:bool=True, queue_state_changes:bool=False):
        if self.serial.in_waiting:
            v = bytearray()
            while self.serial.in_waiting:
                v += self.serial.read(self.serial.in_waiting)
                time.sleep(0.010)
                
            if return_state_reports:
                s = StateChangeReport(v, self._signal_by_address)
                if queue_state_changes:
                    if len(s):
                        self._append_state_change(s)
                    else:
                        print(f'No len rep for {v}')
            return v
        return None
    
    def _append_state_change(self, stch:StateChangeReport):
        self._queued_state_changes.append(tuple([SystemTime.current().clone(), stch]))
        
    def get_queued_state_changes(self):
        v = self._queued_state_changes
        self._queued_state_changes = []
        return v
    
    def get_events(self, test_name:str):
        if test_name not in self.events_of_interest_per_test:
            print(f'No "{test_name}" events found')
            
            print(f'Available: {",".join(self.events_of_interest_per_test.keys())}')
            return 
        event_list = []
        Event.reset_known_variables()
        for ev in self.events_of_interest_per_test[test_name]:
            ev_time = ev[0]
            # print(f'{ev[0]}: ', end='')
            #changes = []
            for changed_field in ev[1].changed():
                s_name = self.aliased_name_for(changed_field)
                ev_val = getattr(ev[1], changed_field)
                event_list.append(Event(ev_time, s_name, ev_val))
                #changes.append(f'{s_name} = {hex(getattr(ev[1], changed_field))}')
                
            #print(','.join(changes))
        return event_list
        
    def write_vcd(self, test_name:str, outputfile_path:str, timescale:str='1 ns'):
        event_list = self.get_events(test_name)
        
        vcd = VCD(event_list, timescale)
        
        for varname in Event.variables_with_events():
            my_field = getattr(self, varname)
            vcd.add_variable(varname, my_field.port.width, 'dut')
            
        vcd.write_to(outputfile_path)
    
    def keepPolling(self):
        while True:
            v = self.poll()
            while v is not None:
                print(v)
                v = self.poll()
            time.sleep(0.001)
            
    
        
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
        self._alias_to_signal[name] = s
        self._signal_name_to_alias = None
        
    def aliased_name_for(self, signal_name:str):
        if self._signal_name_to_alias is None:
            self._signal_name_to_alias = dict()
            for alname,sig in self._alias_to_signal.items():
                self._signal_name_to_alias[sig.port.name] = alname
                
        if signal_name in self._signal_name_to_alias:
            return self._signal_name_to_alias[signal_name]
        
        return signal_name
        
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
            if self.is_monitoring:
                self.poll(queue_state_changes=True)
            return s.read()
        
        def writer(v:int):
            if self.is_monitoring:
                self.poll(queue_state_changes=True)
                chg = StateChangeReport()
                chg.add_change(self.aliased_name_for(name), v)
                self._append_state_change(chg)
            s.write(v)
            if self.is_monitoring:
                time.sleep(0.005)
                self.poll(queue_state_changes=True)
        
        wrt = None
        if s.is_writeable:
            wrt = writer 
            
        iop = SUBIO(s, name, width, reader, wrt)
        setattr(self, name, iop)
        self._signal_by_address[s.address] = iop
        
    
    def testing_will_begin(self):
        # use auto-discover instead self.discover()
        super().testing_will_begin()
        if self.write_test_vcds_to_dir:
            if not self.is_monitoring:
                log.warn(f"Request to write VCDs to '{self.write_test_vcds_to_dir}'--activating monitoring")
                self.is_monitoring = True
        
    
    def testing_unit_done(self, test:microcotb.dut.TestCase):
        for s in self._added_signals.values():
            s.reset()
            
        if self.is_monitoring:
            self.events_of_interest_per_test[test.name] = self.get_queued_state_changes()
            if self.write_test_vcds_to_dir:
                fpath = os.path.join(self.write_test_vcds_to_dir, f'{test.name}.vcd')
                log.warn(f"writing VCD to '{fpath}'")
                try:
                    self.write_vcd(test.name, fpath)
                except:
                    log.error(f"Issue writing VCD file {fpath}")
            
            
        
    @property 
    def is_monitoring(self):
        return self._is_monitoring
    
    @is_monitoring.setter
    def is_monitoring(self, set_to:bool):
        ser = self.serial 
        if set_to:
            bts = bytearray([ord('m'), 1])
            self._is_monitoring = True
        else:
            bts = bytearray([ord('m'), 0])
            self._is_monitoring = False
            
        ser.write(bts)
        print(ser.readline())
        
    def dump_state(self):
        ser = self.serial 
        ser.write(b'd')
        time.sleep(0.3)
        a = b''
        while ser.in_waiting:
            a += ser.read(ser.in_waiting)
            time.sleep(0.05)
        try:
            print(a.decode())
        except:
            pass
        return a
        
    def discover(self):
        log.info('SUB DUT performing discovery')
        ser = self.serial 
        if not ser:
            raise RuntimeError(f'Could not get a serial port on {self.port}')
        if not ser.is_open:
            raise RuntimeError(f'Serial port on {self.port} not open')

        ser.write(b'l')
        time.sleep(0.3)
        a = b''
        while ser.in_waiting:
            a += ser.read(ser.in_waiting)
            time.sleep(0.05)
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


