"""
@package simulator
peer_dbs_video module
"""

# In this implementation, the peer retrieves the first chunks form the
# source because some audio/video codecs (such as Vorbis/Theora) have
# a header. The channel name is provided by the player that performs a
# HTTP GET request (possiblely after an HTTP 302 redirection).

import sys
import struct
from .simulator_stuff import Simulator_socket as socket
from .peer_dbs import Peer_DBS

class Peer_DBS_video(Peer_DBS):

    player_port = 9999
    header_size = 30 # chunks

    #def __init__(self, id, name, loglevel):
    #    super().__init_(id, name, loglevel)

    def wait_for_the_player(self):
        self.player_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.player_socket.bind(('', Peer_DBS_video.player_port))
        self.player_socket.listen(0)
        print("{}: waiting for the player at {}"
              .format(self.id, self.player_socket.getsockname()))
        self.player_socket = self.player_socket.accept()[0]
        #self.player_socket.setblocking(0)
        self.lg.debug("{}: the player is"
                      .format(self.id, self.player_socket.getpeername()))
        GET_bytes = self.player_socket.recv(1024)
        GET = GET_bytes.decode("ascii")
        channel = GET.split('/')[1]
        self.GET_message = 'GET /' + channel + ' HTTP/1.1\r\n'
        self.GET_message += '\r\n'

    # Same function as splitter_dbs_video's one
    def request_the_video_from_the_source(self):
        self.source_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.source_socket.connect(self.source)
        except socket.error as e:
            self.lg.error("{}: Exception: {} from {}".format(self.id,
                                                             e, self.source))
            self.source_socket.close()
            os._exit(1)
        self.lg.debug("{}: connected to {}".format(self.id, self.source))
        self.source_socket.sendall(self.GET_message.encode())
        self.lg.debug("{}: GET_message={}".format(self.id, self.GET_message))

    # Same function as splitter_dbs_video's one
    def receive_header_chunk(self):
        chunk = self.source_socket.recv(self.chunk_size)
        prev_size = 0
        while len(chunk) < self.chunk_size:
            if len(chunk) == prev_size:
                # This section of code is reached when the streaming
                # server (Icecast) finishes a stream and starts with
                # the following one.
                self.lg.debug("{}: No data in the server!".format(self.id))
                sys.stdout.flush()
                self.source_socket.close()
                time.sleep(1)
                self.source_socket = socket.socket(socket.AF_INET,
                                                   socket.SOCK_STREAM)
                self.source_socket.connect(self.source)
                self.source_socket.sendall(self.GET_message.encode())
                #self.header = b""
                #self.header_load_counter = Splitter_DBS_video.header_size
                #_print_("1: header_load_counter =", self.header_load_counter)
                chunk = b""
            prev_size = len(chunk)
            chunk += self.source_socket.recv( - len(chunk))
        return chunk

    def send_chunk_to_player(self):
        try:
            self.player_socket.sendall(self.chunks[chunk_number % self.buffer_size])
        except socket.error:
            self.lg.debug("Player disconnected!")
            self.player_alive = False

    def relay_header_to_player(self):
        print("{}: Relaying the stream header from {} to {}"
              .format(self.id, self.source, self.player))
        for i in range(Peer_DBS_video.header_size*self.chunk_size):
            header_chunk = self.receive_header_chunk()
            #self.send_chunk_to_player(header_chunk)
            self.player_socket.sendall(header_chunk)
            print('.')
            sys.stdout.flush()
        print("{}: header relayed".format(self.id))

    #def load_the_video_header(self):
    #    self.header = b''
    #    for i in range(Splitter_DBS_video.header_size):
    #        self.header += self.receive_next_chunk()

    #def receive_the_header(self):
    #    print("{}: Requesting the stream header to {}"
    #          .format(self.id, self.source))
    #   self.request_the_video_from_the_source()
    #   self.load_the_video_header()
    #   print("{}: Stream header received from {}"
    #         .format(self.id, self.source))


    #def receive_the_header(self):
    #    message = self.splitter_socket.recv(struct.calcsize("H"))
    #    value = struct.unpack("H", message)[0]
    #    self.header_size = socket.ntohs(value)
    #    self.lg.debug("{}: header_size={} chunks"
    #                  .format(self.ext_id, self.header_size))
    #    header_size_in_bytes = self.header_size * self.chunk_size
    #    received = 0
    #    data = ""
    #    while received < header_size_in_bytes:
    #        data = self.splitter_socket.recv(header_size_in_bytes - received)
    #        received += len(data)
    #        self.lg.debug("{}: percentage of header received = {:.2%}"
    #                      .format(sefl.ext_id,
    #                              (1.0*received)/header_size_in_bytes))
    #        self.player_socket.sendall(data)

    def receive_chunk_size(self):
        message = self.splitter_socket.recv(struct.calcsize("H"))
        self.chunk_size = struct.unpack("!H", message)[0]
        #self.chunk_size = socket.ntohs(chunk_size)
        self.lg.debug("{}: chunk_size={}".format(self.id, self.chunk_size))
        self.chunk_packet_format = "!i" + str(self.chunk_size) + "sIi"
        self.max_pkg_length = struct.calcsize(self.chunk_packet_format)
