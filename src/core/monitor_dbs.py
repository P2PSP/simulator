"""
@package simulator
monitor_dbs module
"""

import struct
from .simulator_stuff import Simulator_socket as socket
from .common import Common
from .peer_dbs import Peer_DBS

class Monitor_DBS(Peer_DBS):
    def __init__(self, id, name, loglevel):
        #self.losses = 0
        super().__init__(id, name, loglevel)

    def receive_buffer_size(self):
        Peer_DBS.receive_buffer_size(self)
        # self.buffer_size = self.splitter_socket.recv("H")
        # print(self.id, ": received buffer_size =", self.buffer_size, "from S")
        # self.buffer_size //= 2 # To MRS

        # S I M U L A T I O N
        self.sender_of_chunks = [""] * self.buffer_size

    def complain(self, chunk_number):
        msg = struct.pack("ii", Common.LOST_CHUNK, chunk_number)
        self.team_socket.sendto(msg, self.splitter)
        self.lg.info("{}: [lost chunk {}] sent to {}".format(self.id, chunk_number, self.splitter))

    def request_chunk(self, chunk_number, peer):
        Peer_DBS.request_chunk(self, chunk_number, peer)
        self.complain(chunk_number)

    '''
    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number % self.buffer_size][self.CHUNK] == b"C":
            self.played += 1
        else:
            self.losses += 1
            self.lg.info("{}: lost chunk {}".format(self.id, chunk_number))
            self.complain(chunk_number)
        self.number_of_chunks_consumed += 1
        return self.player_alive
    '''
    def connect_to_the_splitter(self, monitor_port):
        self.lg.debug("{}: connecting to the splitter at {}".format(self.id, self.splitter))
        self.splitter_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.splitter_socket.set_id(self.id) # Ojo, simulation dependant
        #host = socket.gethostbyname(socket.gethostname())
        self.splitter_socket.bind(('', monitor_port))

        try:
            self.splitter_socket.connect(self.splitter)
        except ConnectionRefusedError as e:
            self.lg.error("{}: {}".format(self.id, e))
            raise

        # The index for pending[].
        self.id = self.splitter_socket.getsockname()
        print("{}: I'm a peer".format(self.id))
        #self.neighbor = self.id
        #print("self.neighbor={}".format(self.neighbor))
        #self.pending[self.id] = []

        if __debug__:
            # S I M U L A T I O N
            self.map_peer_type(self.id); # Maybe at the end of this
                                         # function to be easely extended
                                         # in the peer_dbs_sim class.

        self.lg.debug("{}: connected to the splitter".format(self.id))
