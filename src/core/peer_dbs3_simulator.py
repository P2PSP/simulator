"""
@package simulator
peer_dbs3_simulator module
"""

from .peer_dbs2_simulator import Peer_DBS2_simulator

class Peer_DBS3_simulator(Peer_DBS2_simulator):

    def __init__(self, id, name = "Peer_DBS3_simulator"):
        Peer_DBS2_simulator.__init__(self)
        self.lg.debug(f"{name}: DBS3 simulator initialized")
