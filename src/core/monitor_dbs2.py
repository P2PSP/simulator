"""
@package simulator
monitor_dbs2 module
"""

from .monitor_dbs import Monitor_DBS
from .peer_dbs2 import Peer_DBS2

class Monitor_DBS2(Monitor_DBS, Peer_DBS2):
    pass
