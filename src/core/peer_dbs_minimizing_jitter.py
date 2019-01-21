"""
@package simulator
peer_dbs_minimizing_jitter module
"""

import random
from threading import Thread

from .common import Common
from .peer_dbs import Peer_DBS
from .simulator_stuff import Simulator_socket as socket
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import hash


class Peer_DBS_minimizing_jitter(Peer_DBS):

    def __init__(self, id, name, loglevel):
        super().__init__(id, name, loglevel)

    def play_next_chunks(self, last_received_chunk):
        run = last_received_chunk - self.prev_received_chunk
        if abs(run) > 20:
            #self.lg.debug("{}: buffer prev={} last={} play={} run={}".format(self.ext_id, self.prev_received_chunk % self.buffer_size, last_received_chunk % self.buffer_size, self.chunk_to_play % self.buffer_size, run))
            self.request_chunk(last_received_chunk, random.choice(self.team))
        print(run, end=" ")
        for i in range(run):
            #self.player_connected = self.play_chunk(self.chunk_to_play)
            self.play_chunk(self.chunk_to_play)
            #self.chunks[self.chunk_to_play % self.buffer_size] = (-1, b'L', None)
            self.chunk_to_play = (self.chunk_to_play + 1) % Common.MAX_CHUNK_NUMBER
        if ((self.prev_received_chunk % Common.MAX_CHUNK_NUMBER) < last_received_chunk):
            self.prev_received_chunk = last_received_chunk
