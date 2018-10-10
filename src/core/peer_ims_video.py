"""
@package simulator
peer_ims_video module
"""

import netifaces
from selectors import select
import struct
import random
import logging
from .common import Common
from .simulator_stuff import Simulator_socket as socket
from core.peer_dbs_video import Peer_DBS_video

class Peer_IMS_video(Peer_DBS_video):
    pass
