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
import struct
from .ip_tools import IP_tools
from .messages import Messages

class Peer_DBS3(Peer_DBS2):

    def __init__(self):
        Peer_DBS2.__init__(self)
        #self.chunk_potentially_lost = 0

    def set_optimization_horizon(self, optimization_horizon):
        self.optimization_horizon = optimization_horizon

    def set_optimal_neighborhood_degree(self, optimal_neighborhood_degree):
        self.optimal_neighborhood_degree = optimal_neighborhood_degree

    def clear_entry_in_buffer(self, buffer_box):
        return [buffer_box[ChunkStructure.CHUNK_NUMBER], b'L', buffer_box[ChunkStructure.ORIGIN_ADDR], buffer_box[ChunkStructure.ORIGIN_PORT], buffer_box[ChunkStructure.HOPS], buffer_box[ChunkStructure.TIME]]

    def on_chunk_received_from_the_splitter(self, chunk):
        Peer_DBS2.on_chunk_received_from_the_splitter(self, chunk)

        if len(self.team) > 1:
            if len(self.forward[self.public_endpoint]) > 4:
                origin = self.forward[self.public_endpoint][-1]
                peer = random.choice(self.team)
                self.request_origin(origin, peer)
#                stderr.write(" .")
#        if self.number_of_lost_chunks_in_this_round == 0:
#            if len(self.team) > 1:
#                if random.random()>0.0:
#                    # The delayed (but finally received on time) chunk must
#                    # not be requested, neither to the origin of the chunk or
#                    # to me.
#                    peer = random.choice(self.team)
#                    #self.request_path(self.prev_received_chunk, peer)
#                    #chunk_to_request = (self.chunk_to_play-self.buffer_size//2) % self.buffer_size
#                    chunk_to_request = chunk[ChunkStructure.CHUNK_NUMBER] - self.buffer_size // 2
#                    print(chunk_to_request)
#                    self.request_path(chunk_to_request, peer)
#                    stderr.write(" .")
#                    #stderr.write(f"{self.ext_id}: {self.prev_received_chunk} {peer}\n")
#        #self.chunk_potentially_lost = 0

        # Can produce network congestion!
#        for neighbor in self.pending:
#            if len(self.pending[neighbor]) > 0:
#                self.send_chunks(neighbor)

    def __play_chunk(self, chunk_number):
        optimized_chunk = (chunk_number + self.optimization_horizon) % Limits.MAX_CHUNK_NUMBER
        #buffer_box = self.buffer[optimized_chunk % self.buffer_size]
        #if buffer_box[ChunkStructure.CHUNK_DATA] == b'L':
        self.chunk_potentially_lost = optimized_chunk + self.buffer_size//3
        Peer_DBS2.play_chunk(self, chunk_number)

    def request_origin(self, origin, peer):
        #stderr.write(f" R{self.ext_id}-{chunk_number}-{peer}")
        self.lg.debug(f"{self.ext_id}: sent [request_origin {origin}] to {peer}")
        msg = struct.pack("!iIi", Messages.REQUEST_ORIGIN, IP_tools.ip2int(origin[0]), origin[1])
        self.team_socket.sendto(msg, peer)

    def process_request_origin(self, origin, sender):
        stderr.write(f" {colorama.Fore.CYAN}{origin[1]}{colorama.Style.RESET_ALL}")
        self.lg.debug(f"{self.ext_id}: received [request_origin {origin}] from {sender}")
        if origin != sender:
            self.update_forward(origin, sender)
            self.lg.debug(f"{self.ext_id}: process_request: forwarding chunk from {origin} to {sender}")
        else:
            self.lg.debug(f"{self.ext_id}: process_request: origin {origin} is the sender of the request")


#    def process_prune(self, origin, peer):
#        pass
