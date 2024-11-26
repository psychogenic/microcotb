'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from machine import Pin

class PinWrapper:
    def __init__(self, pin):
        self._pin = pin 
        
    @property 
    def value(self):
        return self._pin.value()
    
    @value.setter 
    def value(self, set_to:int):
        #if self._pin.mode != Pin.OUT:
        #    self._pin.mode = Pin.OUT
        self._pin.value(set_to)