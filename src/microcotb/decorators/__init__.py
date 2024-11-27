
import microcotb.platform

if microcotb.platform.IsRP2040:
    from .parametrize_upython import parametrize
else:
    from .parametrize_default import parametrize
    
from .decorators import test