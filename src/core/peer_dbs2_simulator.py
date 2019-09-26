"""
@package simulator
peer_dbs_simulator module
"""

# Specific simulator behavior.

import sys
import struct
import random
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
#from .simulator_stuff import Simulator_socket as socket
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .peer_dbs2 import Peer_DBS2
from .peer_dbs_simulator import Peer_DBS_simulator
import logging
from .chunk_structure import ChunkStructure

#class Peer_DBS2_simulator(Peer_DBS2):
class Peer_DBS2_simulator(Peer_DBS2, Peer_DBS_simulator):

    def __init__(self, id, name = "Peer_DBS2_simulator"):
        Peer_DBS2.__init__(self)
        Peer_DBS_simulator.__init__(self, id, name)
        self.lg.debug(f"{name}: DBS2 initialized")
