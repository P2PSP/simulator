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
from .limits import Limits

class Peer_DBS3(Peer_DBS2):

    def __init__(self):
        Peer_DBS2.__init__(self)
        #self.chunk_potentially_lost = 0

    def set_optimization_horizon(self, optimization_horizon):
        self.optimization_horizon = optimization_horizon

    def set_optimal_neighborhood_degree(self, optimal_neighborhood_degree):
        self.optimal_neighborhood_degree = optimal_neighborhood_degree

    def clear_entry_in_buffer(self, buffer_box):
        return [buffer_box[ChunkStructure.CHUNK_NUMBER], b'L', buffer_box[ChunkStructure.ORIGIN_ADDR], buffer_box[ChunkStructure.ORIGIN_PORT], buffer_box[ChunkStructure.HOPS]]

    def on_chunk_received_from_the_splitter(self, chunk):
        Peer_DBS2.on_chunk_received_from_the_splitter(self, chunk)
        
        if self.number_of_lost_chunks_in_this_round == 0:
            if len(self.team) > 1:
                # The delayed (but finally received on time) chunk must
                # not be requested, neither to the origin of the chunk or
                # to me.
                peer = random.choice(self.team)
                self.request_path(self.prev_received_chunk, peer)
                stderr.write(f"{self.ext_id}: {self.prev_received_chunk} {peer}\n")
        #self.chunk_potentially_lost = 0

        # Can produce network congestion!
        for neighbor in self.pending:
            self.send_chunks(neighbor)

    def __play_chunk(self, chunk_number):
        optimized_chunk = (chunk_number + self.optimization_horizon) % Limits.MAX_CHUNK_NUMBER
        #buffer_box = self.buffer[optimized_chunk % self.buffer_size]
        #if buffer_box[ChunkStructure.CHUNK_DATA] == b'L':
        self.chunk_potentially_lost = optimized_chunk + self.buffer_size//3
        Peer_DBS2.play_chunk(self, chunk_number)
