import math

def get_sim_time(units:str):
    from microcotb.time.system import SystemTime
    current = SystemTime.current()
    return math.ceil(current.time_in(units))