"""
@package simulator
monitor_dbs2_simulator module
"""

from .monitor_dbs_simulator import Monitor_DBS_simulator
from .monitor_dbs2 import Monitor_DBS2

class Monitor_DBS2_simulator(Monitor_DBS_simulator, Monitor_DBS2):
    pass
