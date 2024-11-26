# Copyright (c) 2013 Potential Ventures Ltd
# Copyright (c) 2013 SolarFlare Communications Inc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Potential Ventures Ltd,
#       SolarFlare Communications Inc nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL POTENTIAL VENTURES LTD BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import microcotb.log as logging
from microcotb.types.range import Range
from microcotb.types.logic import Logic
from microcotb.types.logic_array import LogicArray


class _Limits:
    SIGNED_NBIT = 1
    UNSIGNED_NBIT = 2
    VECTOR_NBIT = 3

class HandleBase:
    def __init__(self, handle, path:str=None) -> None:
        self._handle = handle
        self._path: str = self._name if path is None else path
        """The path to this handle, or its name if this is the root handle.

        :meta public:
        """

    @property
    def _name(self) -> str:
        """The name of an object.

        :meta public:
        """
        return self._handle.get_name_string()

    @property
    def _type(self) -> str:
        """The type of an object as a string.

        :meta public:
        """
        return self._handle.get_type_string()
    
    @property
    def _def_name(self) -> str:
        """The name of a GPI object's definition.

        This is the value of ``vpiDefName`` for VPI, ``vhpiNameP`` for VHPI,
        and ``mti_GetPrimaryName`` for FLI.
        Support for this depends on the specific object type and simulator used.

        :meta public:
        """
        return self._handle.get_definition_name()

    @property
    def _log(self):
        """The logging object.

        :meta public:
        """
        return logging.getLogger(f"handle.{self._name}")
    
    
    @property
    def is_const(self) -> bool:
        """``True`` if the simulator object is immutable, e.g. a Verilog parameter or VHDL constant or generic."""
        return self._handle.get_const()


    def __eq__(self, other) -> bool:
        if not isinstance(other, HandleBase):
            return NotImplemented
        return self._handle == other._handle

    def __repr__(self) -> str:
        desc = self._path
        defname = self._def_name
        if defname:
            desc += " with definition " + defname
        return str(type(self)) + "(" + desc + ")"



class RangeableObjectMixin(HandleBase):
    """Base class for simulation objects that have a range."""

    @property
    def range(self) -> Range:
        """Return a :class:`~cocotb.types.Range` over the indexes of the array/vector."""
        left, right, direction = self._handle.get_range()
        if direction == Range.RANGE_NO_DIR:
            raise RuntimeError("Expected range to have a direction but got none!")
        return Range(left, "to" if direction == Range.RANGE_UP else "downto", right)

    @property
    def left(self) -> int:
        """Return the leftmost index in the array/vector."""
        return self.range.left

    @property
    def direction(self) -> str:
        """Return the direction (``"to"``/``"downto"``) of indexes in the array/vector."""
        return self.range.direction

    @property
    def right(self) -> int:
        """Return the rightmost index in the array/vector."""
        return self.range.right

    def __len__(self) -> int:
        return len(self.range)


class LogicObject(
    RangeableObjectMixin,
):
    def __init__(self, handle:HandleBase, path:str=None) -> None:
        super().__init__(handle, path)

    def _set_value(
        self,
        value, #: Union[LogicArray, Logic, int, str],
        # action, #: _GPISetAction,
        schedule_write
    ) -> None:
        value_: str
        if isinstance(value, int):
            min_val, max_val = _value_limits(len(self), _Limits.VECTOR_NBIT)
            if min_val <= value <= max_val:
                if len(self) <= 32:
                    schedule_write(
                        self, self._handle.set_signal_val_int, (value,)
                    )
                    return

                # LogicArray used for checking
                if value < 0:
                    value_ = str(
                        LogicArray.from_signed(
                            value,
                            Range(len(self) - 1, "downto", 0),
                        )
                    )
                else:
                    value_ = str(
                        LogicArray.from_unsigned(
                            value,
                            Range(len(self) - 1, "downto", 0),
                        )
                    )
            else:
                raise ValueError(
                    f"Int value ({value!r}) out of range for assignment of {len(self)!r}-bit signal ({self._name!r})"
                )

        elif isinstance(value, str):
            # LogicArray used for checking
            value_ = str(LogicArray(value, self.range))

        elif isinstance(value, LogicArray):
            if len(self) != len(value):
                raise ValueError(
                    f"cannot assign value of length {len(value)} to handle of length {len(self)}"
                )
            value_ = str(value)

        elif isinstance(value, Logic):
            if len(self) != 1:
                raise ValueError(
                    f"cannot assign value of length 1 to handle of length {len(self)}"
                )
            value_ = str(value)

        else:
            raise TypeError(
                f"Unsupported type for value assignment: {type(value)} ({value!r})"
            )

        schedule_write(self, self._handle.set_signal_val_binstr, (value_, ))

    @property
    def value(self) -> LogicArray:
        binstr = self._handle.get_signal_val_binstr()
        return LogicArray._from_handle(binstr, on_change=lambda newval: self.set(newval))

    @value.setter
    def value(self, value: LogicArray) -> None:
        self.set(value)


    def set(
        self,
        value# : Union[ValueSetT, Deposit[ValueSetT], Force[ValueSetT], Freeze, Release],
    ) -> None:
        if self.is_const:
            raise TypeError(f"{self._path} is constant")

        #value_, action = _map_action_obj_to_value_action_enum_pair(self, value)

        #import cocotb._write_scheduler

        # self._set_value(value_, action, cocotb._write_scheduler.schedule_write)
        self._set_value(value, schedule_write_immediate)
        

    def __getitem__(self, key:int):
        return self.value[key]
    
    def __setitem__(self, key:int, value):
        v = self.value 
        if isinstance(key, slice):
            if isinstance(value, int):
                if value < 0:
                    new_value = LogicArray.from_signed(value, width=len(v[key]))
                else:
                    new_value = LogicArray.from_unsigned(value, width=len(v[key]))
            elif isinstance(value, (bytes, bytearray)):
                new_value = LogicArray.from_bytes(value, width=len(v[key]))
            elif isinstance(value, LogicArray):
                if len(value) != len(v[key]):
                    raise OverflowError(f"Assignment array len ({len(value)}) != slice width ({len(v[key])})")
                new_value = value
            elif isinstance(value, list):
                if len(value) != len(v[key]):
                    raise OverflowError(f"Assignment array len ({len(value)}) != slice width ({len(v[key])})")
                new_value = value
            else: 
                raise TypeError(
                    f"Unsupported type for item value assignment: {type(value)} ({value!r})"
                )
        elif isinstance(key, int):
            new_value = value 
        else:
            raise KeyError(
                f"Unsupported type for item key: {type(key)} ({key!r})"
            )
        v[key] = new_value
        self.set(v)

def schedule_write_immediate(caller:LogicObject, setter, args):
    setter(args[0])

def _value_limits(n_bits: int, limits: _Limits):
    """Calculate min/max for given number of bits and limits class"""
    if limits == _Limits.SIGNED_NBIT:
        min_val = -(2 ** (n_bits - 1))
        max_val = 2 ** (n_bits - 1) - 1
    elif limits == _Limits.UNSIGNED_NBIT:
        min_val = 0
        max_val = 2**n_bits - 1
    else:
        min_val = -(2 ** (n_bits - 1))
        max_val = 2**n_bits - 1

    return min_val, max_val
