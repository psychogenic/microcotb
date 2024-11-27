'''
Created on Nov 27, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''
from .parametrized import Parameterized
def parametrize(options_by_name_dict):

    options = list(options_by_name_dict.items())
    def wrapper(f) -> Parameterized:
        return Parameterized(f, options)

    return wrapper