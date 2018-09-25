"""
@package simulator
peer_dbs_max_degree_latency module
"""

import struct
import random
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import Simulator_socket as socket
from .peer_dbs_latency import Peer_DBS_latency
from .peer_dbs_max_degree import Peer_DBS_max_degree

class Peer_DBS_max_degree_latency(Peer_DBS_latency, Peer_DBS_max_degree):
    pass
