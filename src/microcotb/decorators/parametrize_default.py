'''
Created on Nov 27, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from .parametrized import Parameterized
def parametrize(*options_by_tuple, **options_by_name):
    options = []
    if len(options_by_tuple):
        for i, option_by_tuple in enumerate(options_by_tuple):
            if len(option_by_tuple) != 2:
                raise ValueError(
                    f"Invalid option tuple {i}, expected exactly two fields `(name, values)`"
                )
            options.extend((option_by_tuple,))
    
    options.extend(options_by_name.items())
    def wrapper(f) -> Parameterized:
        return Parameterized(f, options)

    return wrapper