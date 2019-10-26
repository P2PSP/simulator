"""
@package simulator
peer_dbs3 module
"""

# Abstract class

# DBS3 (Data Broadcasting Set extension 2) layer, peer side.

# DBS3 extends DBS2, optimizing the topology even when not chunks are
# lost.

import random
from .chunk_structure import ChunkStructure
from .peer_dbs import Peer_DBS
from .peer_dbs2 import Peer_DBS2
import colorama
import core.stderr as stderr

class Peer_DBS3(Peer_DBS2):

    def __init__(self):
        Peer_DBS2.__init__(self)

    def set_optimization_horizon(self, optimization_horizon):
        self.optimization_horizon = optimization_horizon

    def set_optimal_neighborhood_degree(self, optimal_neighborhood_degree):
        self.optimal_neighborhood_degree = optimal_neighborhood_degree

    def on_chunk_received_from_the_splitter(self, chunk):
        self.Peer_DBS2.on_chunk_received_from_the_splitter(chunk)
        if len(self.team) > 1:
            # The delayed (but finally received on time) chunk must
            # not be requested, neither to the origin of the chunk or
            # to me.
            peer = random.choice(self.team)
            while peer == (self.buffer[ChunkStructure.ORIGIN_ADDR],
                           self.buffer[ChunkStructure.ORIGIN_PORT]):
                peer = random.choice(self.team)
            self.request_path(self.chunk_potentially_lost, peer)

    def play_chunk(self, chunk_number):
        optimized_chunk = (chunk_number + self.optimization_horizon) % Limits.MAX_CHUNK_NUMBER
        buffer_box = self.buffer[optimized_chunk % self.buffer_size]
        if buffer_box[ChunkStructure.CHUNK_DATA] == b'L':
            self.chunk_potentially_lost = optimized_chunk
        self.Peer_DBS2.play_chunk(chunk_number)
