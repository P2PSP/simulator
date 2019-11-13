"""
@package simulator
peer_dbs3_simulator module
"""


from .peer_dbs3 import Peer_DBS3
from .peer_simulator import Peer_simulator

class Peer_DBS3_simulator(Peer_DBS3, Peer_simulator):

    def __init__(self, id, name = "Peer_DBS3_simulator"):
        Peer_DBS3.__init__(self)
        Peer_simulator.__init__(self, id, name)
        self.lg.debug(f"{name}: initialized")
