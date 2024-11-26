# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause

class Range:
    RANGE_DOWN = -1
    RANGE_NO_DIR = 0
    RANGE_UP = 1
    def __init__(
        self,
        left: int,
        direction= None,
        right = None,
    ) -> None:
        start = left
        stop: int
        step: int
        if isinstance(direction, int) and right is None:
            step = _guess_step(left, direction)
            stop = direction + step
        elif isinstance(direction, str) and isinstance(right, int):
            step = _direction_to_step(direction)
            stop = right + step
        elif direction is None and isinstance(right, int):
            step = _guess_step(left, right)
            stop = right + step
        else:
            raise TypeError("invalid arguments")
        self._range = range(start, stop, step)

    @classmethod
    def from_range(cls, range: range) -> "Range":
        """Convert :class:`range` to :class:`Range`."""
        return cls(
            left=range.start,
            direction=_step_to_direction(range.step),
            right=(range.stop - range.step),
        )

    def to_range(self) -> range:
        """Convert Range to :class:`range`."""
        return self._range

    @property
    def left(self) -> int:
        """Leftmost value in a Range."""
        return self._range.start

    @property
    def direction(self) -> str:
        """``'to'`` if Range is ascending, ``'downto'`` otherwise."""
        return _step_to_direction(self._range.step)

    @property
    def right(self) -> int:
        """Rightmost value in a Range."""
        return self._range.stop - self._range.step

    def __len__(self) -> int:
        return len(self._range)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._range[item]
        elif isinstance(item, slice):
            return type(self).from_range(self._range[item])
        raise TypeError(
            f"indices must be integers or slices, not {type(item).__name__}"
        )

    def __contains__(self, item: object) -> bool:
        return item in self._range

    def __iter__(self):
        return iter(self._range)

    def __reversed__(self):
        return reversed(self._range)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, type(self)):
            return self._range == other._range
        return NotImplemented  # must not be in a type narrowing context to be ignored properly

    def __hash__(self) -> int:
        return hash(self._range)

    def __repr__(self) -> str:
        return f"{type(self).__qualname__}({self.left!r}, {self.direction!r}, {self.right!r})"

    # index = cached_method(Sequence.index)
    def index(self, idx:int) -> int:
        return list(self._range).index(idx)

def _guess_step(left: int, right: int) -> int:
    if left <= right:
        return 1
    return -1


def _direction_to_step(direction: str) -> int:
    direction = direction.lower()
    if direction == "to":
        return 1
    elif direction == "downto":
        return -1
    raise ValueError("direction must be 'to' or 'downto'")


def _step_to_direction(step: int) -> str:
    if step == 1:
        return "to"
    elif step == -1:
        return "downto"
    raise ValueError("step must be 1 or -1")
