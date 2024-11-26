from .features import Features
from .detection import IsRP2040

if IsRP2040:
    from .rp2040 import *
else:
    from .dummy import *