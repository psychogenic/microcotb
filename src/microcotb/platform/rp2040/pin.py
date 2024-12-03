'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from machine import Pin

class PinWrapper:
    def __init__(self, name:str, pin):
        self._pin = pin 
        self._name = name 
        
    @property 
    def name(self):
        return self._name
        
        
    @property 
    def value(self):
        return self._pin.value()
    
    @value.setter 
    def value(self, set_to:int):
        #if self._pin.mode != Pin.OUT:
        #    self._pin.mode = Pin.OUT
        self._pin.value(set_to)
        
    def __repr__(self):
        return f'<Pin {self._name}'