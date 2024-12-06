'''
Created on Nov 26, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
class Features:
    SleepMsUs = False
    TicksUs = False
    FunctionsHaveQualifiedNames = False
    ExceptionsHaveTraceback = False
    
def dummyfunc():
    print()
    

    
Features.FunctionsHaveQualifiedNames = hasattr(dummyfunc, '__qualname__')

try:
    raise Exception('boink')
except Exception as e:
    if hasattr(e, '__traceback__'):
        Features.ExceptionsHaveTraceback = True