'''
Created on Dec 8, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''


class WithValue:
    def __init__(self, val=None):
        self._value = val
        
    @property 
    def value(self):
        return self._value
    
    @value.setter 
    def value(self, set_to:int):
        self._value = set_to
        
    def __int__(self):
        return int(self.value)

    def __bool__(self):
        return bool(int(self.value))
    
    def __eq__(self, other):
        return self.value == other
    def __ne__(self, other):
        return self.value != other
    
    def __lt__(self, other):
        return self.value < other
    def __le__(self, other):
        return self.value <= other
    def __gt__(self, other):
        return self.value > other
    def __ge__(self, other):
        return self.value >= other

        