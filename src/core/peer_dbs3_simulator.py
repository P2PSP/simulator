"""
@package simulator
peer_dbs3_simulator module
"""

from .peer_dbs2_simulator import Peer_DBS2_simulator
from .peer_dbs3 import Peer_DBS3

class Peer_DBS3_simulator(Peer_DBS2_simulator, Peer_DBS3):

    def __init__(self, id, name = "Peer_DBS3_simulator"):
        Peer_DBS3.__init__(self)
        Peer_DBS2_simulator.__init__(self, id)
        self.lg.debug(f"{name}: DBS3 simulator initialized")
