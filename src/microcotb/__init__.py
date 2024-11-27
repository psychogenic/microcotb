from .runner import Runner
from .decorators import test, parametrize

def start_soon(c):
    pass

def get_runner(sim=None):
    return Runner.get()
