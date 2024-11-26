from .pin import PinWrapper
from ..features import Features

Features.SleepMsUs = True
Features.TicksUs = True

import sys 
import io
def exception_as_str(e:Exception):
    buf = io.StringIO()
    sys.print_exception(e, buf)
    return buf.getvalue()