'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from microcotb.types.with_value import WithValue

class PinWrapper(WithValue):
    def __init__(self, name:str, pin=None):
        super().__init__(0)
        self._pin = pin 
        self._name = name
        
    def __hash__(self)->int:
        return hash(self._name)
    @property 
    def name(self):
        return self._name
        
    def __repr__(self):
        return f'<Pin {self.name}>'
        

