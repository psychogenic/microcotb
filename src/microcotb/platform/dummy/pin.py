'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
class PinWrapper:
    def __init__(self, name:str, pin=None):
        self._pin = pin 
        self._name = name
        self._value = 0
        
    @property 
    def name(self):
        return self._name
        
        
    @property 
    def value(self):
        return self._value
    
    @value.setter 
    def value(self, set_to:int):
        self._value = set_to
        
    def __repr__(self):
        return f'<Pin {self.name}>'
        

