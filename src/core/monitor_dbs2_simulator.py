"""
@package simulator
monitor_dbs2_simulator module
"""

from .monitor_dbs2 import Monitor_DBS2
from .peer_simulator import Peer_simulator

class Monitor_DBS2_simulator(Monitor_DBS2, Peer_simulator):
    def __init__(self, id, name = "Monitor_DBS2_simulator"):
        Monitor_DBS2.__init__(self)
        Peer_simulator.__init__(self, id, name)
        self.lg.debug(f"{name}: initialized")
