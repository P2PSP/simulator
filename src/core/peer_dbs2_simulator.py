"""
@package simulator
peer_dbs2_simulator module
"""

from .peer_dbs2 import Peer_DBS2
from .peer_simulator import Peer_simulator

class Peer_DBS2_simulator(Peer_DBS2, Peer_simulator):

    def __init__(self, id, name = "Peer_DBS2_simulator"):
        Peer_DBS2.__init__(self)
        Peer_DBS_simulator.__init__(self, id, name)
        self.lg.debug(f"{name}: DBS2 simulator initialized")

