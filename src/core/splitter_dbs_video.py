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

    channel = "BBB-144.ogv"

    def __init__(self, name):
        supper().__init__(id, name)

        self.CHUNK_SIZE = 1024 # In bytes
        self.HEADER_SIZE = 30 # In chunks
        
        self.SOURCE_ADDR = "localhost"
        self.SOURCE_PORT = 8000
        
        self.source = (self.SOURCE_ADDR, self.SOURCE_PORT)
        self.GET_message = 'GET /' + self.CHANNEL + ' HTTP/1.1\r\n'
        self.GET_message += '\r\n'

        self.header_load_counter = 0
        self.chunk_packet_format = "!i1024sIi"

        self.lg.debug("{}: initialized".format(self.id))

def receive_next_chunk(self):
    chunk = self.source_socket.recv(self.CHUNK_SIZE)
    prev_size = 0
    while len(chunk) < self.CHUNK_SIZE:
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
            self.header = b""
            self.header_load_counter = self.HEADER_SIZE
            #_print_("1: header_load_counter =", self.header_load_counter)
            chunk = b""
        prev_size = len(chunk)
        chunk += self.source_socket.recv(self.CHUNK_SIZE - len(chunk))
    return chunk

    def receive_chunk(self):
        chunk = self.receive_next_chunk()
        if self.header_load_counter > 0:
            self.header += chunk
            self.header_load_counter -= 1
            self.lg.debug("{}: Loaded {} bytes of header"
                          .format(self.id, len(self.header)))
        self.chunk_counter += 1
        return chunk

    def compose_message(self, chunk, peer):
        chunk_msg = (self.chunk_number, chunk, socket.ip2int(peer[0]),peer[1])
        msg = struct.pack("!isIi", *chunk_msg)
        return msg

    def request_the_video_from_the_source(self):
        self.source_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.source_socket.connect(self.source)
        except socket.error as e:
            self.lg.error("{}: Exception: {}".format(self.id, e))
            self.source_socket.close()
            os._exit(1)
        self.lg.debug("{}: connected to {}".format(self.id, self.source))
        self.source_socket.sendall(self.GET_message.encode())
        self.lg.debug("{}: GET_message={}".format(self.id, self.GET_message))

    def load_the_video_header(self):
        self.header = b''
        for i in range(self.HEADER_SIZE):
            self.header += self.receive_next_chunk()

    def receive_the_header(self):
        self.lg.debug("{}: Requesting the stream header ...".format(self.id))

        self.request_the_video_from_the_source()
        self.load_the_video_header()

        self.lg.debug("{}: Stream header received!".format(self.id))

