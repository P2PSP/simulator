"""
@package simulator
peer_ims module
"""

# IMS (Ip Multicast Set) of rules

# When the list of peers is received from the splitter, for all those
# peers that share the same network address that the peer, the
# endpoint 224.0.0.1:1234 will be used. Thus, when the peer receives a
# chunk from the splitter, it will forward it to this multicast
# channel (all hosts multicast group). The rest of the logic is identical?

import netifaces
from selectors import select
import struct
import random
import logging
from .common import Common
from .simulator_stuff import Simulator_socket as socket
from core.peer_dbs import Peer_DBS
from core.peer_dbs_simulator import Peer_DBS_simulator

class Peer_IMS_simulator(Peer_DBS_simulator):
    pass
