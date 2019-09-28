"""
@package simulator
peer_dbs_simulator module
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

class Peer_DBS_simulator(Peer_DBS):

    def __init__(self, id, name = "Peer_DBS_simulator"):
        super().__init__()
        self.lg.debug(f"{name}: DBS initialized")

    def receive_the_chunk_size(self):
        pass

    def packet_format(self):
        self.chunk_packet_format = "!isIii"

    def compose_message(self, chunk_number):
        chunk_position = chunk_number % self.buffer_size
        chunk = self.buffer[chunk_position]
        stored_chunk_number = chunk[ChunkStructure.CHUNK_NUMBER]
        chunk_data = chunk[ChunkStructure.CHUNK_DATA]
        chunk_origin_IP = chunk[ChunkStructure.ORIGIN][0]
        chunk_origin_port = chunk[ChunkStructure.ORIGIN][1]
        hops = chunk[ChunkStructure.ORIGIN+1]
        content = (stored_chunk_number, chunk_data, IP_tools.ip2int(chunk_origin_IP), chunk_origin_port, hops+1)
        #self.compose_message__show(chunk_position, chunk_number)
        self.lg.debug(f"{self.ext_id}: chunk_position={chunk_position} chunk_number={self.buffer[chunk_position][ChunkStructure.CHUNK_NUMBER]} origin={self.buffer[chunk_position][ChunkStructure.ORIGIN]} hops={self.buffer[chunk_position][ChunkStructure.ORIGIN+1]}")
        packet = struct.pack(self.chunk_packet_format, *content)
        return packet

    def unpack_chunk(self, packet):
        message = struct.unpack(self.chunk_packet_format, packet)
        message = message[ChunkStructure.CHUNK_NUMBER], message[ChunkStructure.CHUNK_DATA], (IP_tools.int2ip(message[ChunkStructure.ORIGIN]), message[ChunkStructure.ORIGIN+1]), message[ChunkStructure.ORIGIN+2]
        return message

    def clear_entry_in_buffer(self):
        return (buffer_box[ChunkStructure.CHUNK_NUMBER], b'L', buffer_box[ChunkStructure.ORIGIN], buffer_box[ChunkStructure.ORIGIN+1])

    def init_entry_in_buffer(self):
        return (-1, b'L', (None, 0), 0)
