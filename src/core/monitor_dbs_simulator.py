"""
@package simulator
monitor_dbs module
"""

from .monitor_dbs import Monitor_DBS
from .peer_dbs_simulator import Peer_DBS_simulator

class Monitor_DBS_simulator(Monitor_DBS, Peer_DBS_simulator):
    pass
