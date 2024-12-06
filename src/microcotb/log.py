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
        def warning(self, s):
            self.out(s, WARN)
        def error(self, s):
            self.out(s, ERROR)
            
        def getChild(self, name):
            return getLogger(f'{self.name}.{name}')
        
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
    COLORS = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "grey"]
    class ColourFormatter(Formatter):
        
        grey = f"\x1b[3{COLORS.index('grey')};20m"
        red = f"\x1b[3{COLORS.index('red')};20m"
        bold_red = f"\x1b[3{COLORS.index('red')};1m"
        yellow = f"\x1b[3{COLORS.index('yellow')};20m"
        blue = f"\x1b[3{COLORS.index('blue')};20m"
        magenta = f"\x1b[3{COLORS.index('magenta')};20m"
        white = f"\x1b[3{COLORS.index('white')};20m"
        cyan = f"\x1b[3{COLORS.index('cyan')};20m"
        green = f"\x1b[3{COLORS.index('green')};20m"
        reset = "\x1b[0m"
        format = "[%(levelno)s] %(name)s %(message)s"
    
        FORMATS = {
            DEBUG: grey + format + reset,
            INFO: green + format + reset,
            WARNING: yellow + format + reset,
            ERROR: red + format + reset,
            CRITICAL: bold_red + format + reset
        }
    
        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = Formatter(log_fmt)
            return formatter.format(record)
        
        
    class ColouredLogger(Logger):
        def __init__(self, name):
            super().__init__(name)                
    
            color_formatter = ColourFormatter()
    
            console = StreamHandler()
            console.setFormatter(color_formatter)
            self.propagate = False
            self.addHandler(console)
            
            return
    
    setLoggerClass(ColouredLogger)
    root_logger = getLogger()
    for hndl in root_logger.handlers:
        root_logger.removeHandler(hndl)
    
    