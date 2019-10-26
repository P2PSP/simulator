"""
@package simulator
monitor_dbs3_simulator module
"""

from .monitor_dbs2_simulator import Monitor_DBS2_simulator
from .peer_dbs3 import Peer_DBS3

class Monitor_DBS3_simulator(Monitor_DBS2_simulator, Peer_DBS3):
    pass
