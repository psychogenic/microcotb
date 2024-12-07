'''
Created on Dec 7, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

class StateChangeReport:
    '''
        Base interface for a State Change Report.
    '''
    def __init__(self):
        self._changed_ports = dict()
        self._num_changes = 0
    def add_change(self, pname:str, pvalue:int):
        self._changed_ports[pname] = pvalue
        setattr(self, pname, pvalue)
        self._num_changes += 1
        return self
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
            
  
  
class StateCache:
    
    def __init__(self):
        self.last_vals = dict() 
        
    def clear(self):
        self.last_vals = dict() 
        
    
    def change_event(self, s:StateChangeReport):
        for sig, val in s.all_changes():
            self.last_vals[sig] = val
            
    def has(self, name:str):
        return name in self.last_vals 
    
    def get(self, signame:str):
        return self.last_vals[signame]
    def set(self, signame:str, val):
        self.last_vals[signame] = val
            