# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-

from math import ceil, log2

from microcotb.types.array import ArrayLike
from microcotb.types.logic import Logic, _str_literals
from microcotb.types.range import Range

def bit_length(val:int):
    return ceil(log2(val+1))

class LogicArray(ArrayLike):

    # These three attribute contain the current value of the array in one or more of
    # three different implementations. This is done for performance reasons, as certain
    # implementations are faster for particular operations.
    # Each implementation can be present, or None if the implementation has not been
    # computed or has been invalidated by a mutating operation.
    _value_as_array = None
    _value_as_int = None
    _value_as_str = None
    _range: Range = None

    def __init__(
        self,
        value = None,
        range = None,
        *,
        width = None,
        on_change = None
    ) -> None:
        self._value_as_array = None
        self._value_as_int = None
        self._value_as_str = None
        self._on_change_callback = on_change
        range = _make_range(range, width)
        if isinstance(value, str):
            if not (set(value) <= _str_literals):
                raise ValueError("Invalid str literal")
            self._value_as_str = value.upper()
            if range is not None:
                if len(value) != len(range):
                    raise OverflowError(
                        f"Value of length {len(self._value_as_str)} will not fit in {range}"
                    )
                self._range = range
            else:
                self._range = Range(len(self._value_as_str) - 1, "downto", 0)
        elif isinstance(value, int):
            if value < 0:
                raise ValueError("Invalid int literal")
            if range is None:
                raise TypeError("Missing required arguments: 'range' or 'width'")
            bitlen = max(1, bit_length(value))
            if bitlen > len(range):
                raise OverflowError(
                    f"{value!r} will not fit in a LogicArray with bounds: {range!r}."
                )
            self._value_as_int = value
            self._range = range
        elif value is None:
            if range is None:
                raise TypeError("Missing required arguments: 'range' or 'width'")
            self._value_as_str = "X" * len(range)
            self._range = range
        else:
            self._value_as_array = [Logic(v) for v in value]
            if range is not None:
                if len(self._value_as_array) != len(range):
                    raise OverflowError(
                        f"Value of length {len(self._value_as_array)} will not fit in {range}"
                    )
                self._range = range
            else:
                self._range = Range(len(self._value_as_array) - 1, "downto", 0)

    def _get_array(self) -> list:
        if self._value_as_array is None:
            # May convert int to str before to converting to array.
            self._value_as_array = [Logic(v) for v in self._get_str()]
        return self._value_as_array

    def _get_str(self) -> str:
        if self._value_as_str is None:
            if self._value_as_int is not None:
                fstr = '{val:0' + str(len(self)) + 'b}'
                self._value_as_str = fstr.format(val=self._value_as_int)
            else:
                self._value_as_str = "".join(
                    str(v) for v in list(self._value_as_array)
                )
        return self._value_as_str

    def _get_int(self) -> int:
        if self._value_as_int is None:
            # May convert list to str before converting to int.
            self._value_as_int = int(self._get_str(), 2)
        return self._value_as_int

    @classmethod
    def from_unsigned(
        cls,
        value: int,
        range = None,
        *,
        width = None,
    ) -> "LogicArray":
        
        range = _make_range(range, width)
        if range is None:
            raise TypeError("Missing required arguments: 'range' or 'width'")
        return LogicArray(value, range)

    @classmethod
    def from_signed(
        cls,
        value: int,
        range = None,
        *,
        width = None,
    ) -> "LogicArray":
        
        range = _make_range(range, width)
        if range is None:
            raise TypeError("Missing required arguments: 'range' or 'width'")
        if value < 0:
            value += 2 ** len(range)
        # If value doesn't fit in range, it will still be negative and will blow the
        # constructor up in a bad way.
        if value < 0:
            raise OverflowError(
                f"{value!r} will not fit in a LogicArray with bounds: {range!r}."
            )
        return LogicArray(value, range)


    @classmethod
    def from_bytes(
        cls,
        value, #  Union[bytes, bytearray],
        range  = None,
        *,
        width = None, # Union[int, None] = None,
        byteorder = "big",
    ) -> "LogicArray":
        range = _make_range(range, width)
        if range is None:
            range = Range(len(value) * 8 - 1, "downto", 0)
        elif len(value) * 8 != len(range):
            raise OverflowError(
                f"Value of length {len(value)} will not fit in a LogicArray with bounds: {range!r}"
            )
        return cls.from_unsigned(
            int.from_bytes(value, byteorder, False), range
        )

    @classmethod
    def _from_handle(cls, value: str, on_change=None) -> "LogicArray":
        # Used by cocotb.handle classes to make LogicArray from values gotten from the
        # simulator which we expect to be well-formed.
        # Values are required to be uppercase.
        self = super().__new__(cls)
        self._value_as_array = None
        self._value_as_int = None
        self._value_as_str = value
        self._on_change_callback = on_change
        self._range = Range(len(value) - 1, "downto", 0)
        return self

    @property
    def range(self) -> Range:
        """:class:`Range` of the indexes of the array."""
        return self._range

    @range.setter
    def range(self, new_range: Range) -> None:
        """Set a new indexing scheme on the array. Must be the same size."""
        if not isinstance(new_range, Range):
            raise TypeError("range argument must be of type 'Range'")
        if len(new_range) != len(self):
            raise ValueError(
                f"{new_range!r} not the same length as old range: {self._range!r}."
            )
        self._range = new_range

    def __iter__(self):
        return iter(self._get_array())

    def __reversed__(self):
        return reversed(self._get_array())

    def __contains__(self, item: object) -> bool:
        return item in self._get_array()

    def __eq__(
        self,
        other: object,
    ) -> bool:
        if isinstance(other, int):
            try:
                return self.to_unsigned() == other
            except ValueError:
                return False
        elif isinstance(other, str):
            return str(self) == other.upper()
        elif isinstance(other, LogicArray):
            if len(self) != len(other):
                return False
            # Complex, but efficient chain of checking logic.
            # Avoid conversions if it can help it at first.
            # Prefers checking against str vs any type since that is going to be the
            #   most common type and also the "middle" type for conversions.
            # Always converts away from ints to prevent issues with non-0/1 data.
            if self._value_as_str is not None and other._value_as_str is not None:
                # (STR, STR)
                return self._value_as_str == other._value_as_str
            elif self._value_as_array is not None and other._value_as_array is not None:
                # (ARRAY, ARRAY)
                return self._value_as_array == other._value_as_array
            elif self._value_as_int is not None and other._value_as_int is not None:
                # (INT, INT)
                return self._value_as_int == other._value_as_int
            elif self._value_as_str is not None:
                # (STR, INT)
                # (STR, ARRAY)
                return self._value_as_str == other._get_str()
            elif other._value_as_str is not None:
                # (INT, STR)
                # (ARRAY, STR)
                return self._get_str() == other._value_as_str
            elif self._value_as_array is not None:
                # (ARRAY, INT)
                return self._value_as_array == other._get_array()
            else:
                # (INT, ARRAY)
                return self._get_array() == other._value_as_array
        elif isinstance(other, (list, tuple)):
            try:
                other = LogicArray(other)
            except ValueError:
                return False
            return self == other
        else:
            return NotImplemented
        
    def __gt__(self, other):
        return int(self) > int(other)
    
    def __ge__(self, other):
        return int(self) >= int(other)
    
    def __lt__(self, other):
        return int(self) < int(other)
    def __le__(self, other):
        return int(self) <= int(other)
        

    @property
    def is_resolvable(self) -> bool:
        """``True`` if all elements are ``0`` or ``1``."""
        return all(bit in (Logic(0), Logic(1)) for bit in self)

    def to_unsigned(self) -> int:
        if len(self) == 0:
            # warnings.warn("Converting a LogicArray of length 0 to integer")
            return 0
        return self._get_int()

    def to_signed(self) -> int:
        if len(self) == 0:
            # warnings.warn("Converting a LogicArray of length 0 to integer")
            return 0
        value = self._get_int()
        if value >= (1 << (len(self) - 1)):
            value -= 1 << len(self)
        return value

    def to_bytes(
        self,
        byteorder  = "big",
    ) -> bytes:
        return self.to_unsigned().to_bytes(ceil(len(self) / 8), byteorder)

    def __getitem__(self, item):
        array = self._get_array()
        if isinstance(item, int):
            idx = self._translate_index(item)
            return array[idx]
        elif isinstance(item, slice):
            start = item.start if item.start is not None else self.left
            stop = item.stop if item.stop is not None else self.right
            if item.step is not None:
                raise IndexError("do not specify step")
            start_i = self._translate_index(start)
            stop_i = self._translate_index(stop)
            if start_i > stop_i:
                raise IndexError(
                    f"slice [{start}:{stop}] direction does not match array direction [{self.left}:{self.right}]"
                )
            value = array[start_i : stop_i + 1]
            range = Range(start, self.direction, stop)
            return LogicArray(value=value, range=range, on_change=self._on_change_callback)
        raise TypeError(f"indexes must be ints or slices, not {type(item).__name__}")

    def __setitem__(
        self,
        item,
        value,
    ) -> None:
        array = self._get_array()
        # invalid other impls
        self._value_as_str = None
        self._value_as_int = None
        if isinstance(item, int):
            idx = self._translate_index(item)
            array[idx] = Logic(value)
        elif isinstance(item, slice):
            start = item.start if item.start is not None else self.left
            stop = item.stop if item.stop is not None else self.right
            if item.step is not None:
                raise IndexError("do not specify step")
            start_i = self._translate_index(start)
            stop_i = self._translate_index(stop)
            if start_i > stop_i:
                raise IndexError(
                    f"slice [{start}:{stop}] direction does not match array direction [{self.left}:{self.right}]"
                )
            
            slice_width = (stop_i - start_i + 1)
            if isinstance(value, int):
                if value < 0:
                    value_as_logics = list(LogicArray.from_signed(value, width=slice_width))
                else:
                    value_as_logics = list(LogicArray.from_unsigned(value, width=slice_width))
            else:
                value_as_logics = [
                    Logic(v) for v in iter(value)
                ]
                
            if len(value_as_logics) != slice_width:
                raise ValueError(
                    f"value of length {len(value_as_logics)!r} will not fit in slice [{start}:{stop}]"
                )
            array[start_i : stop_i + 1] = value_as_logics
        else:
            raise TypeError(
                f"indexes must be ints or slices, not {type(item).__name__}"
            )
        
        if self._on_change_callback is not None:
            self._on_change_callback(self)

    def _translate_index(self, item: int) -> int:
        try:
            return self._range.index(item)
        except ValueError:
            raise IndexError(f"index {item} out of range") from None

    def __repr__(self) -> str:
        return f"<LogicArray({str(self)!r}, {self.range!r})>"

    def __str__(self) -> str:
        return self._get_str()

    def __bin__(self):
        return f'0b{str(self)!r}'
    
    def __int__(self) -> int:
        return self.to_unsigned()

    def __index__(self) -> int:
        return int(self)

    def __and__(self, other: "LogicArray") -> "LogicArray":
        if isinstance(other, int):
            # Allow &= ~x to work
            other &= (1 << len(self)) - 1
            return LogicArray(value=(other & self.to_unsigned()), range=self._range)
        if not isinstance(other, LogicArray):
            return NotImplemented
        if len(self) != len(other):
            raise ValueError(
                "cannot perform bitwise & "
            )
        return LogicArray(a & b for a, b in zip(self, other))

    def __or__(self, other: "LogicArray") -> "LogicArray":
        if isinstance(other, int):
            return LogicArray(value=(other | self.to_unsigned()), range=self._range)
        if not isinstance(other, LogicArray):
            return NotImplemented
        if len(self) != len(other):
            raise ValueError(
                f"cannot perform bitwise | "
            )
        return LogicArray(a | b for a, b in zip(self, other))

    def __xor__(self, other: "LogicArray") -> "LogicArray":
        if isinstance(other, int):
            return LogicArray(value=(other ^ self.to_unsigned()), range=self._range)
        if not isinstance(other, LogicArray):
            return NotImplemented
        if len(self) != len(other):
            raise ValueError(
                f"cannot perform bitwise ^ "
            )
        return LogicArray(a ^ b for a, b in zip(self, other))

    def __invert__(self) -> "LogicArray":
        return LogicArray(~v for v in self)

    def __bool__(self) -> bool:
        return any(v in (Logic("H"), Logic("1")) for v in self)


def _make_range(
    range, width #  Union[int, None]
    ):
    if width is not None:
        if range is not None:
            raise TypeError("Only provide argument to one of 'range' or 'width'")
        return Range(width - 1, "downto", 0)
    elif isinstance(range, int):
        return Range(range - 1, "downto", 0)
    elif range is None or isinstance(range, Range):
        return range
    else:
        raise TypeError(
            f"Expected Range for parameter 'range', not {type(range)}"
        )
