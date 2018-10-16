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
    #def play_chunk(self, chunk_number):
    #    if self.chunks[chunk_number % self.buffer_size][Common.CHUNK_NUMBER] > -1:
    #        self.player_socket.sendall(self.chunks[chunk_number % self.buffer_size][Common.CHUNK_DATA])
    #        self.chunks[chunk_number % self.buffer_size] = (-1, b'L', None)
    #        self.played += 1
    #        print('o', end=''); sys.stdout.flush()
    #    else:
    #        self.losses += 1
    #        self.lg.critical("{}: lost chunk! {} (losses = {})".format(self.ext_id, chunk_number, self.losses))
    #    self.number_of_chunks_consumed += 1
