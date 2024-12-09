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
    def changed(self):
        '''
            return a list of names of things that have changed
        '''
        return list(self._changed_ports.keys())     
    def all_changes(self):
        '''
            returns a list of tuples of (name, current_value)
        '''
        return list(self._changed_ports.items())
    def get(self, name:str):
        '''
            returns the value for the 'name' item 
        '''
        if not self.has(name):
            return None
        return self._changed_ports[name]
    def has(self, name:str):
        '''
            return whether this report has a value for 'name'
        '''
        return name in self._changed_ports
    
    def add_change(self, pname:str, pvalue:int):
        '''
            used internally to add a new changed value.
        '''
        self._changed_ports[pname] = pvalue
        setattr(self, pname, pvalue)
        self._num_changes += 1
        return self
    def __len__(self):
        return len(self._changed_ports)
    def __repr__(self):
        num_changed_io = len(self._changed_ports)
        if self._num_changes > num_changed_io:
            # some changes were overwritten here
            return f'<StateChangeReport with {num_changed_io} (in {self._num_changes}) changes>'
        return f'<StateChangeReport with {num_changed_io} changes>'
    
    def __str__(self):
        outlist = []
        for k,v in self._changed_ports.items():
            outlist.append(f'{k} = {hex(v)} ({bin(v)})')
        if not len(outlist):
            return 'StateChangeReport: no changes'
        
        num_changed_io = len(outlist)
        outdeets = '\n  '.join(outlist)
        addenda = ''
        if self._num_changes > num_changed_io:
            addenda = f' in {self._num_changes}'
        return f"StateChangeReport ({num_changed_io}{addenda}):\n{outdeets}"
            
  
  
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
            