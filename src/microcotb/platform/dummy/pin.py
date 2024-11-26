'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
class PinWrapper:
    def __init__(self, pin=None):
        self._pin = pin 
        self._value = 0
        
    @property 
    def value(self):
        return self._value
    
    @value.setter 
    def value(self, set_to:int):
        self._value = set_to
        

