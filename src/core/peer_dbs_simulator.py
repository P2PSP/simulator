"""
@package simulator
peer_dbs_simulator module
"""

# Specific simulator behavior. In the simulator, peers do not play
# the stream.

import time
import sys
import struct
import random
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
#from .simulator_stuff import Simulator_socket as socket
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .peer_dbs import Peer_DBS
import logging
#import colorama
from .chunk_structure import ChunkStructure

class Peer_DBS_simulator(Peer_DBS):

    def __init__(self, id, name = "Peer_DBS_simulator"):
        super().__init__()
        self.lg.debug(f"{name}: DBS initialized")

    def receive_the_chunk_size(self):
        pass
