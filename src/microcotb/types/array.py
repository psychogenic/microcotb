# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause
from microcotb.types.range import Range


class ArrayLike:
    @property
    def left(self) -> int:
        """Leftmost index of the array."""
        return self.range.left

    @property
    def direction(self) -> str:
        """``"to"`` if indexes are ascending, ``"downto"`` otherwise."""
        return self.range.direction

    @property
    def right(self) -> int:
        """Rightmost index of the array."""
        return self.range.right

    @property
    def range(self) -> Range:
        """:class:`Range` of the indexes of the array."""

    @range.setter
    def range(self, new_range: Range) -> None:
        """Set a new indexing scheme on the array.

        Must be the same size.
        """

    def __len__(self) -> int:
        return len(self.range)

    def __iter__(self):
        for i in self.range:
            yield self[i]

    def __reversed__(self):
        for i in reversed(self.range):
            yield self[i]

    def __contains__(self, item: object) -> bool:
        for v in self:
            if v == item:
                return True
        return False

    def index(
        self,
        value,
        start = None,
        stop = None,
    ) -> int:
        """Find first occurence of value.

        Args:
            value: Value to search for.
            start: Index to start search at.
            stop: Index to stop search at.

        Returns: Index of first occurence of *value*.

        Raises:
            ValueError: If the value is not present.
        """
        if start is None:
            start = self.left
        if stop is None:
            stop = self.right
        for i in Range(start, self.direction, stop):
            if self[i] == value:
                return i
        raise IndexError(f"{value!r} not in array")

    def count(self, value) -> int:
        """Return number of occurrences of value.

        Args:
            value: Value to search for.

        Returns: Number of occurences of *value*.
        """
        count: int = 0
        for v in self:
            if v == value:
                count += 1
        return count




class Array(ArrayLike):

    def __init__(
        self,
        value,
        range = None,
        width = None,
    ) -> None:
        self._value = list(value)
        if width is not None:
            if range is not None:
                raise TypeError("Only provide argument to one of 'range' or 'width'")
            self._range = Range(0, "to", width - 1)
        elif range is None:
            self._range = Range(0, "to", len(self._value) - 1)
        elif isinstance(range, int):
            self._range = Range(0, "to", range - 1)
        elif isinstance(range, Range):
            self._range = range
        else:
            raise TypeError(
                f"Expected Range or int for parameter 'range', not {type(range).__qualname__}"
            )
        if len(self._value) != len(self._range):
            raise ValueError(
                f"Value of length {len(self._value)!r} does not fit in {self._range!r}"
            )

    @property
    def range(self) -> Range:
        """:class:`Range` of the indexes of the array."""
        return self._range

    @range.setter
    def range(self, new_range: Range) -> None:
        """Sets a new indexing scheme on the array, must be the same size"""
        if not isinstance(new_range, Range):
            raise TypeError("range argument must be of type 'Range'")
        if len(new_range) != len(self):
            raise ValueError(
                f"{new_range!r} not the same length as old range ({self._range!r})."
            )
        self._range = new_range

    def __iter__(self):
        return iter(self._value)

    def __reversed__(self):
        return reversed(self._value)

    def __contains__(self, item: object) -> bool:
        return item in self._value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Array):
            return self._value == other._value
        elif isinstance(other, (list, tuple)):
            return self == Array(other)
        else:
            return NotImplemented

    def __getitem__(self, item):
        if isinstance(item, int):
            idx = self._translate_index(item)
            return self._value[idx]
        elif isinstance(item, slice):
            start = item.start if item.start is not None else self.left
            stop = item.stop if item.stop is not None else self.right
            if item.step is not None:
                raise IndexError("do not specify step")
            start_i = self._translate_index(start)
            stop_i = self._translate_index(stop)
            
            # print(f'Slice {item} with start {start} stop {stop} {start_i}/{stop_i}')
            if start_i > stop_i:
                raise IndexError(
                    f"slice [{start}:{stop}] direction does not match array direction [{self.left}:{self.right}]"
                )
            value = self._value[start_i : stop_i + 1]
            range = Range(start, self.direction, stop)
            return Array(value=value, range=range)
        raise TypeError(f"indexes must be ints or slices, not {type(item).__name__}")
        
    def __setitem__(
        self, item, value
    ) -> None:
        if isinstance(item, int):
            idx = self._translate_index(item)
            self._value[idx] = value
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
            value = list(iter(value))
            if len(value) != (stop_i - start_i + 1):
                raise ValueError(
                    f"value of length {len(value)!r} will not fit in slice [{start}:{stop}]"
                )
            self._value[start_i : stop_i + 1] = value
        else:
            raise TypeError(
                f"indexes must be ints or slices, not {type(item).__name__}"
            )

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._value!r}, {self._range!r})"

    def _translate_index(self, item: int) -> int:
        try:
            return self._range.index(item)
        except ValueError:
            raise IndexError(f"index {item} out of range") from None
