"""
@package simulator
monitor_strpeds module
"""

from .peer_strpeds import Peer_STRPEDS
from .simulator_stuff import Simulator_socket as socket
from .common import Common
import struct

class Monitor_STRPEDS(Peer_STRPEDS):
    def __init__(self, id):
        self.losses = 0
        super().__init__(id)
        print("STRPEDS initialized by monitor")

    def receive_buffer_size(self):

        Peer_STRPEDS.receive_buffer_size(self)
        self.buffer_size //= 2

        # --- Only for simulation purposes ----
        self.sender_of_chunks = [""] * self.buffer_size
        # -------------------------------------

    def complain(self, chunk_number):
        msg = struct.pack("ii", Common.REQUEST, chunk_number)
        self.team_socket.sendto(msg, self.splitter)
        self.lg.info("{}: [request {}] sent to {}".format(self.id, chunk_number, self.splitter))

    def request_chunk(self, chunk_number, peer):
        Peer_STRPEDS.request_chunk(self, chunk_number, peer)
        self.complain(chunk_number)

'''    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number % self.buffer_size][1] == "C":
            self.played += 1
        else:
            self.losses += 1
            print(self.id, ": lost Chunk!", chunk_number)
            self.complain(chunk_number)
        self.number_of_chunks_consumed += 1
        return self.player_alive
    '''