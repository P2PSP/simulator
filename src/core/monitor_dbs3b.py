"""
@package simulator
monitor_dbs2 module
"""

from .monitor_dbs2 import Monitor_DBS2
from .peer_dbs3b import Peer_DBS3

class Monitor_DBS3(Monitor_DBS2, Peer_DBS3):
    def __init__(self):
        Peer_DBS3.__init__(self)
        Monitor_DBS2.__init__(self)

