"""
@package simulator
peer_dbs_simulator module
"""

# Specific simulator behavior.

import time
import struct
import logging
import random
import netifaces
from threading import Thread
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import Simulator_socket as socket
from .simulator_stuff import hash
from .peer_dbs import Peer_DBS

# quitar
MAX_DEGREE = 5

class Peer_DBS_simulator(Peer_DBS):
    pass
