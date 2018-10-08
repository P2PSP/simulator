"""
@package p2psp-simulator
splitter_dbs module
"""

# DBS (Data Broadcasting Set) layer

# DBS is the most basic layer to provide communication among splitter
# (source of the stream) and peers (destination of the stream), using
# unicast transmissions. The splitter sends a different chunk of
# stream to each peer, using a random round-robin scheduler.

# TODO: In each round peers are selected at random, but all peers are
# sent a chunk, in a round).

import os
import time
import struct
import logging
from .simulator_stuff import Simulator_socket as socket
from .splitter_dbs import Splitter_DBS

class Splitter_DBS_video(Splitter_DBS):

    def __init__(self, name):
        supper().__init__(id, name)

        self.SOURCE_ADDR = "localhost"
        self.SOURCE_PORT = 8000
        
        self.source = (self.SOURCE_ADDR, self.SOURCE_PORT)
        self.GET_message = 'GET /' + self.CHANNEL + ' HTTP/1.1\r\n'
        self.GET_message += '\r\n'
        
        self.lg.debug("{}: initialized".format(self.id))

    def receive_chunk(self):
        # Simulator_stuff.LOCK.acquire(True,0.1)
        time.sleep(Common.CHUNK_CADENCE)  # Simulates bit-rate control
        # C -> Chunk, L -> Loss, G -> Goodbye, B -> Broken, P -> Peer, M -> Monitor, R -> Ready
        return b'C'

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

