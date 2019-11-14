"""
@package simulator
peer_simulator module
"""

# Specific simulator behavior. In the simulator, peers do not play
# the stream.

import time
import sys
import struct
import random
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
#from .simulator_stuff import Simulator_socket as socket
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .peer_dbs import Peer_DBS
import logging
#import colorama
from .chunk_structure import ChunkStructure
from .ip_tools import IP_tools
from .messages import Messages
import core.stderr as stderr

class Peer_simulator():

    def __init__(self, id, name = "Peer_Simulator"):
        self.rounds_counter = 0
        self.accumulated_latency_in_the_round = 0
        self.number_of_chunks_received_in_the_round = 0
        self.lg.debug(f"{name}: initialized")

    def receive_the_chunk_size(self):
        pass

    def set_packet_format(self):
        self.packet_format = "!isIiid"

    def clear_entry_in_buffer(self, buffer_box):
        return [buffer_box[ChunkStructure.CHUNK_NUMBER], b'L', buffer_box[ChunkStructure.ORIGIN_ADDR], buffer_box[ChunkStructure.ORIGIN_PORT], buffer_box[ChunkStructure.HOPS], buffer_box[ChunkStructure.TIME]]
        #return [buffer_box[ChunkStructure.CHUNK_NUMBER], b'L', buffer_box[ChunkStructure.ORIGIN_ADDR], buffer_box[ChunkStructure.ORIGIN_PORT], buffer_box[ChunkStructure.HOPS], time.time()]
        #return self.empty_entry_in_buffer()

    def empty_entry_in_buffer(self):
        return [-1, b'L', None, 0, 0, 0.0] # chunk_number, chunk, (source), hops, time
        #return [-1, b'L', None, 0, 0, time.time()] # chunk_number, chunk, (source), hops, time

    def on_chunk_received_from_a_peer__(self, chunk, sender):
        super().on_chunk_received_from_a_peer(chunk, sender)
        self.number_of_chunks_received_in_the_round += 1

    def compute_average_latency__(self):
        average_latency = self.accumulated_latency_in_the_round / self.number_of_chunks_received_in_the_round
        self.accumulated_latency_in_the_round = 0
        self.lg.debug(f"{self.ext_id}: average_latency={average_latency} -- {self.number_of_chunks_received_in_the_round} --")

    def on_chunk_received_from_the_splitter__(self, chunk):
        su.on_chunk_received_from_the_splitter(chunk)
        self.rounds_counter += 1
        self.number_of_chunks_received_in_the_round += 1
        self.compute_average_latency()
        self.number_of_chunks_received_in_the_round = 0
