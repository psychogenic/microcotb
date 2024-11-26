# Copyright cocotb contributors
# Licensed under the Revised BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-3-Clause


_U = 0
_X = 1
_0 = 2
_1 = 3
_Z = 4
_W = 5
_L = 6
_H = 7
_D = 8

_literal_repr  = {
    # unassigned
    "U": _U,
    "u": _U,
    # unknown
    "X": _X,
    "x": _X,
    # 0
    0: _0,  # Also `False`
    "0": _0,
    # 1
    1: _1,  # Also `True`
    "1": _1,
    # high impedance
    "Z": _Z,
    "z": _Z,
    # weak unknown
    "W": _W,
    "w": _W,
    # weak 0
    "L": _L,
    "l": _L,
    # weak 1
    "H": _H,
    "h": _H,
    # don't care
    "-": _D,
}

_str_literals  = {k for k in _literal_repr.keys() if isinstance(k, str)}


class Logic:

    _repr: int

    @classmethod
    def _get_object(cls, _repr: int) -> "Logic":
        """Return the Logic object associated with the repr, enforcing singleton."""
        self = object.__new__(cls)
        self._repr = _repr
        return self

    @classmethod
    def _map_literal(
        cls,
        value = None,
    ) -> "Logic":
        """Convert and cache all literals."""
        if value is None:
            _repr = _X
        else:
            # convert literal
            try:
                _repr = _literal_repr[value]
            except KeyError:
                raise ValueError(
                    f"{value!r} is not convertible to a {cls}"
                ) from None
        obj = cls._get_object(_repr)
        return obj

    def __new__(
        cls,
        value = None,
    ) -> "Logic":
        if isinstance(value, Logic):
            return value
        elif value is not None and not isinstance(value, (str, int, bool)):
            raise TypeError(
                f"Expected str, bool, or int, not {type(value)}"
            )
        return cls._map_literal(value)

    def __and__(self, other: "Logic") -> "Logic":
        if not isinstance(other, Logic):
            return NotImplemented
        return Logic(
            (
                # -----------------------------------------------------
                # U    X    0    1    Z    W    L    H    -       |   |
                # -----------------------------------------------------
                ("U", "U", "0", "U", "U", "U", "0", "U", "U"),  # | U |
                ("U", "X", "0", "X", "X", "X", "0", "X", "X"),  # | X |
                ("0", "0", "0", "0", "0", "0", "0", "0", "0"),  # | 0 |
                ("U", "X", "0", "1", "X", "X", "0", "1", "X"),  # | 1 |
                ("U", "X", "0", "X", "X", "X", "0", "X", "X"),  # | Z |
                ("U", "X", "0", "X", "X", "X", "0", "X", "X"),  # | W |
                ("0", "0", "0", "0", "0", "0", "0", "0", "0"),  # | L |
                ("U", "X", "0", "1", "X", "X", "0", "1", "X"),  # | H |
                ("U", "X", "0", "X", "X", "X", "0", "X", "X"),  # | - |
            )[self._repr][other._repr]
        )

    def __or__(self: "Logic", other: "Logic") -> "Logic":
        if not isinstance(other, Logic):
            return NotImplemented
        return Logic(
            (
                # -----------------------------------------------------
                # U    X    0    1    Z    W    L    H    -       |   |
                # -----------------------------------------------------
                ("U", "U", "U", "1", "U", "U", "U", "1", "U"),  # | U |
                ("U", "X", "X", "1", "X", "X", "X", "1", "X"),  # | X |
                ("U", "X", "0", "1", "X", "X", "0", "1", "X"),  # | 0 |
                ("1", "1", "1", "1", "1", "1", "1", "1", "1"),  # | 1 |
                ("U", "X", "X", "1", "X", "X", "X", "1", "X"),  # | Z |
                ("U", "X", "X", "1", "X", "X", "X", "1", "X"),  # | W |
                ("U", "X", "0", "1", "X", "X", "0", "1", "X"),  # | L |
                ("1", "1", "1", "1", "1", "1", "1", "1", "1"),  # | H |
                ("U", "X", "X", "1", "X", "X", "X", "1", "X"),  # | - |
            )[self._repr][other._repr]
        )

    def __xor__(self: "Logic", other: "Logic") -> "Logic":
        if not isinstance(other, Logic):
            return NotImplemented
        return Logic(
            (
                # -----------------------------------------------------
                # U    X    0    1    Z    W    L    H    -       |   |
                # -----------------------------------------------------
                ("U", "U", "U", "U", "U", "U", "U", "U", "U"),  # | U |
                ("U", "X", "X", "X", "X", "X", "X", "X", "X"),  # | X |
                ("U", "X", "0", "1", "X", "X", "0", "1", "X"),  # | 0 |
                ("U", "X", "1", "0", "X", "X", "1", "0", "X"),  # | 1 |
                ("U", "X", "X", "X", "X", "X", "X", "X", "X"),  # | Z |
                ("U", "X", "X", "X", "X", "X", "X", "X", "X"),  # | W |
                ("U", "X", "0", "1", "X", "X", "0", "1", "X"),  # | L |
                ("U", "X", "1", "0", "X", "X", "1", "0", "X"),  # | H |
                ("U", "X", "X", "X", "X", "X", "X", "X", "X"),  # | - |
            )[self._repr][other._repr]
        )

    def __invert__(self: "Logic") -> "Logic":
        return Logic(("U", "X", "1", "0", "X", "X", "1", "0", "X")[self._repr])

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Logic):
            return self._repr == other._repr
                
        elif isinstance(other, (int, str, bool)):
            try:
                other = Logic(other)
            except ValueError:
                return False
            return self == other
        else:
            return NotImplemented

    def __repr__(self) -> str:
        return f"<Logic ({str(self)!r})>"

    def __str__(self) -> str:
        return ("U", "X", "0", "1", "Z", "W", "L", "H", "-")[self._repr]

    def __bool__(self) -> bool:
        if self._repr == _0:
            return False
        elif self._repr == _1:
            return True
        raise ValueError(f"Cannot convert {self!r} to bool")

    def __int__(self) -> int:
        if self._repr == _0:
            return 0
        elif self._repr == _1:
            return 1
        raise ValueError(f"Cannot convert {self!r} to int")
    
    

    def __index__(self) -> int:
        return int(self)
