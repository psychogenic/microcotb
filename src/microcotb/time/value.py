'''
Created on Nov 23, 2024

@author: Pat Deegan
@copyright: Copyright (C) 2024 Pat Deegan, https://psychogenic.com
'''

class TimeConverter:
    UnitScales = {
                'fs': 1e-15,
                'ps': 1e-12,
                'ns': 1e-9,
                'us': 1e-6,
                'ms': 1e-3,
                'sec': 1
            }
    Units = ['fs', 'ps', 'ns', 'us', 'ms', 'sec']
    
    @classmethod 
    def scale(cls, units:str):
        if units not in cls.UnitScales:
            raise ValueError(f"Unknown units {units}")
        return cls.UnitScales[units]
    
    @classmethod 
    def time_to_clockticks(cls, clock, t:int, units:str):
        tval = TimeValue(t, units)
        return round(tval / clock.period)
    
    @classmethod 
    def rescale(cls,t:int, units:str, to_units:str):
        if units == to_units:
            return t
        return t*(cls.scale(units)/cls.scale(to_units))
    
    @classmethod 
    def units_step_down(cls, units:str):
        try:
            idx = cls.Units.index(units)
        except:
            return None 
        
        if idx < 1:
            return None 
        return cls.Units[idx - 1]
    
    @classmethod 
    def units_step_up(cls, units:str):
        try:
            idx = cls.Units.index(units)
        except:
            return None 
        
        if idx >= (len(cls.Units) - 1):
            return None 
        return cls.Units[idx + 1]
    
        
    
class TimeValue:
    ReBaseStringUnits = False # go up units in str repr
    BaseUnits = 'ns'
    def __init__(self, time:int, units:str):
        self._time = time 
        self._units = units
        self.scale = TimeConverter.scale(units)
        self._as_float = None
        self._store_baseunits()
        if units != self.BaseUnits and \
            TimeConverter.UnitScales[units] < TimeConverter.UnitScales[self.BaseUnits]:
            raise RuntimeError(f'Reduce TimeValue.BaseUnits to {units}')
        
    def _store_baseunits(self):
        if self.units == self.BaseUnits:
            self._t_baseunits = self.time 
        else:
            self._t_baseunits = int(TimeConverter.rescale(self.time, self.units, self.BaseUnits))
        
    def clone(self):
        return TimeValue(self.time, self.units)
    @property 
    def time(self):
        return self._time 
    
    @time.setter 
    def time(self, set_to:int):
        self._time = set_to 
        self._as_float = None
    @property 
    def units(self):
        return self._units 
    @units.setter 
    def units(self, set_to:str):
        self._units = set_to 
        self.scale = TimeConverter.scale(set_to)
        self._as_float = None
        
    def time_in(self, units:str):
        if units == self.units:
            return self.time
        return TimeConverter.rescale(self.time, self.units, units)
    
    def cast_stepdown_units(self):
        smaller_units = TimeConverter.units_step_down(self.units)
        if smaller_units is None:
            return None 
        return TimeValue(self.time*1000, smaller_units)
        
    def _directly_comparable(self, other):
        return isinstance(other, TimeValue) and other.units == self.units 
    
    def __float__(self):
        if self._as_float is None:
            self._as_float = self.time*self.scale
        return self._as_float
    
    def __gt__(self, other):
        return self._t_baseunits > other._t_baseunits
    
    def __lt__(self, other):
        return self._t_baseunits < other._t_baseunits
    def __le__(self, other):
        return self._t_baseunits <= other._t_baseunits
    
    def __ge__(self, other):
        return self._t_baseunits >= other._t_baseunits
    
    def __eq__(self, other):
        return self._t_baseunits == other._t_baseunits
    
    def __iadd__(self, other):
        if self._directly_comparable(other):
            self.time += other.time
            self._store_baseunits()
            return self
        
        if isinstance(other, TimeValue):
            self.time += TimeConverter.rescale(other.time, other.units, self.units)
            self._store_baseunits()
            return self
        raise ValueError
    
    def __add__(self, other):
        if self._directly_comparable(other):
            return TimeValue(self.time + other.time, self.units)
        
        if isinstance(other, TimeValue):
            new_time = self.time + TimeConverter.rescale(other.time, other.units, self.units)
            return TimeValue(new_time, self.units)
        raise ValueError
    
    def __repr__(self):
        return f'<TimeValue {round(self.time)} {self.units}>'
    
    def __str__(self):
        if not self.ReBaseStringUnits:
            return f'{round(self.time)}{self.units}'
        
        v = TimeValue(self.time, self.units)
        while v.time >= 1000:
            up_units = TimeConverter.units_step_up(v.units)
            if up_units:
                v = TimeValue(TimeConverter.rescale(self.time, self.units, up_units), up_units)
        return f'{v.time:.4f}{v.units}'
    
    def __truediv__(self, other):
        if isinstance(other, TimeValue):
            other_conv = TimeConverter.rescale(other.time, other.units, self.units)
            return self.time / other_conv
        raise ValueError
    
    def __mul__(self, other:int):
        return TimeValue(self.time*other, self.units)
        