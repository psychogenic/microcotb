'''
Created on Nov 27, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

from microcotb.runner import TestCase
def iter_product(*iterables, repeat=1):
    if repeat < 0:
        raise ValueError('no negative repeats')
    pools = [tuple(pool) for pool in iterables] * repeat
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]
        
    for prod in result:
        yield tuple(prod)

class Parameterized:
    def __init__(self,func, options):
        self.test_function = func
        self.__name__ = func.__name__
        self.options = options
        #self.test_function_runner = None
    def generate_tests(self,
        *,
        name:str = None,
        timeout_time:float = None,
        timeout_unit: str = "us",
        expect_fail: bool = False,
        expect_error:Exception = (),
        skip: bool = False,
        stage: int = 0,
        ):
        test_func_name = self.test_function.__name__ if name is None else name
        option_indexes = [range(len(option[1])) for option in self.options]
        for selected_options in iter_product(*option_indexes, repeat=1):
            test_kwargs = {}
            test_name_pieces  = [test_func_name]
            for option_idx, select_idx in enumerate(selected_options):
                option_name, option_values = self.options[option_idx]
                selected_value = option_values[select_idx]

                if isinstance(option_name, str):
                    # single params per option
                    #selected_value = list(selected_value)
                    test_kwargs[option_name] = selected_value
                    test_name_pieces.append(
                        f"/{option_name}={test_kwargs[option_name]}"
                    )
                else:
                    # multiple params per option
                    #selected_value = list(selected_value)
                    for n, v in zip(option_name, selected_value):
                        test_kwargs[n] = v
                        test_name_pieces.append(
                            f"/{n}={self._option_reprs[n][select_idx]}"
                        )
                        
            parametrized_test_name = "".join(test_name_pieces)

            # create wrapper function to bind kwargs
            async def run_my_test(dut, kwargs=test_kwargs) -> None:
                await self.test_function(dut, **kwargs)

            yield TestCase(
                func=run_my_test,
                name=parametrized_test_name,
                timeout_time=timeout_time,
                timeout_unit=timeout_unit,
                expect_fail=expect_fail,
                expect_error=expect_error,
                skip=skip,
                stage=stage
            )
