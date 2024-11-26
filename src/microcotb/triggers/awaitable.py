'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''


class Awaitable:
    def __init__(self, signal=None):
        self.signal = signal
    
    def __iter__(self):
        return self

    def __next__(self): 
        raise StopIteration