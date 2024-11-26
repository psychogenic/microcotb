'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

 
from microcotb.platform import IsRP2040
DefaultLogLevel = 20 # info by default
if IsRP2040:
    uLoggers = dict()
    # no logging support, add something basic
    DEBUG = 10
    INFO = 20
    WARN = 30
    ERROR = 40
    class Logger:
        def __init__(self, name):
            self.name = name 
            self.loglevel = DefaultLogLevel
        def out(self, s, level:int):
            if self.loglevel <= level:
                print(f'{self.name}: {s}')
            
        def debug(self, s):
            self.out(s, DEBUG)
        def info(self, s):
            self.out(s, INFO)
        def warn(self, s):
            self.out(s, WARN)
        def error(self, s):
            self.out(s, ERROR)
        
    def getLogger(name:str):
        global uLoggers
        if name not in uLoggers:
            uLoggers[name] = Logger(name)
        return uLoggers[name]
    
    def basicConfig(level:int):
        global DefaultLogLevel
        global uLoggers
        DefaultLogLevel = level
        for logger in uLoggers.values():
            logger.loglevel = level
            
        
else:
    from logging import *