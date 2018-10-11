"""
@package p2psp-simulator
splitter_dbs_video module
"""

# Implements video transmissions.

import os
import time
import struct
import logging
from .simulator_stuff import Simulator_socket as socket
from .splitter_dbs import Splitter_DBS

class Splitter_DBS_video(Splitter_DBS):

    channel = "LBBB.ogv"
    buffer_size = 128
    chunk_size = 1024
    #header_size = 30
    source_address = "localhost"
    source_port = 8000

    def __init__(self, name):
        super().__init__(name)
        
        self.source = (Splitter_DBS_video.source_address,
                       Splitter_DBS_video.source_port)
        self.GET_message = 'GET /' + Splitter_DBS_video.channel + ' HTTP/1.1\r\n'
        self.GET_message += '\r\n'

        #self.header_load_counter = 0
        self.chunk_packet_format = "!i" \
            + str(Splitter_DBS_video.chunk_size) \
            + "sIi"

        self.lg.debug("{}: initialized".format(self.id))

    def send_the_chunk_size(self):
        self.lg.debug("{}: Sending chunk_size={}"
                      .format(self.id, Splitter_DBS.chunk_size))
        message = struct.pack("!H", socket.htons(self.CHUNK_SIZE))
        peer_serve_socket.sendall(message)

    def receive_next_chunk(self):
        chunk = self.source_socket.recv(Splitter_DBS_video.chunk_size)
        prev_size = 0
        while len(chunk) < Splitter_DBS_video.chunk_size:
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

    def receive_chunk(self):
        chunk = self.receive_next_chunk()
        #if self.header_load_counter > 0:
        #    self.header += chunk
        #    self.header_load_counter -= 1
        #    self.lg.debug("{}: Loaded {} bytes of header"
        #                  .format(self.id, len(self.header)))
        self.chunk_counter += 1
        return chunk

