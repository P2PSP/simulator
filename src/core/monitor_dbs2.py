"""
@package simulator
monitor_dbs2 module
"""

from .monitor_dbs import Monitor_DBS
from .peer_dbs2 import Peer_DBS2

class Monitor_DBS2(Monitor_DBS, Peer_DBS2):
    def __init__(self):
        Peer_DBS2.__init__(self)
        Monitor_DBS.__init__(self)

