"""
@package simulator
peer_dbs module
"""

import struct
from .simulator_stuff import Simulator_socket as socket
from .peer_dbs import Peer_DBS

class Peer_DBS_video(Peer_DBS):

    player_port = 9999

    #def __init__(self, id, name, loglevel):
    #    super().__init_(id, name, loglevel)

    def send_chunk_to_player(self):
        try:
            self.player_socket.sendall(self.chunks[chunk_number % self.buffer_size])
        except socket.error:
            self.lg.debug("Player disconnected!")
            self.player_alive = False

    def wait_for_the_player(self):
        self.player_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.player_socket.bind(('', Peer_DBS_video.player_port))
        self.player_socket.listen(0)
        self.lg.debug("{}: waiting for the player at {}"
                      .format(self.id, self.player_socket.getsockname()))
        self.player_socket = self.player_socket.accept()[0]
        #self.player_socket.setblocking(0)
        self.lg.debug("{}: the player is"
                      .format(self.id, self.player_socket.getpeername()))

    def receive_the_header(self):
        message = self.splitter_socket.recv(struct.calcsize("H"))
        value = struct.unpack("H", message)[0]
        self.header_size = socket.ntohs(value)
        self.lg.debug("{}: header_size={} chunks"
                      .format(self.ext_id, self.header_size))
        header_size_in_bytes = self.header_size * self.chunk_size
        received = 0
        data = ""
        while received < header_size_in_bytes:
            data = self.splitter_socket.recv(header_size_in_bytes - received)
            received += len(data)
            self.lg.debug("{}: percentage of header received = {:.2%}"
                          .format(sefl.ext_id,
                                  (1.0*received)/header_size_in_bytes))
            self.player_socket.sendall(data)

    def receive_the_chunk_size(self):
        message = self.splitter_socket.recv(struct.calcsize("H"))
        chunk_size = struct.unpack("H", message)[0]
        self.chunk_size = socket.ntohs(chunk_size)
        self.lg.debug("{}: chunk_size={}".format(self.ext_id, self.chunk_size))
        self.message_format = "H" + str(self.chunk_size) + "s"


