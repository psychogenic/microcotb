from .runner import Runner
from .decorators import test, parametrize
from microcotb.platform import Features
import os

RunnerModuleName = 'default'

def start_soon(c):
    pass

def get_runner(module_name:str=None, sim=None):
    if module_name is None:
        module_name = get_caller_file(2)
    return Runner.get(module_name)

def get_caller_file(back_levels:int=1):
    if not Features.ExceptionsHaveTraceback:
        return RunnerModuleName
    
    try:
        raise Exception('boink')
    except Exception as e:
        if not hasattr(e, '__traceback__'):
            return RunnerModuleName
        
        frame = e.__traceback__.tb_frame
        
        for _i in range(back_levels):
            frame = frame.f_back 
        
        fname =  os.path.splitext(os.path.basename(frame.f_code.co_filename))[0]
        return fname
        
