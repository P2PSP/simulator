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
from .messages import Messages
import core.stderr as stderr

class Peer_DBS_simulator(Peer_DBS):

    def __init__(self, id, name = "Peer_DBS_simulator"):
        super().__init__()
#        self.chunk_packet_format = "!isIii"
        self.lg.debug(f"{name}: DBS simulator initialized")

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

    def unpack_message(self, packet, sender):
        msg_format = "!i" + (len(packet)-4)*'s'
        chunk_number, *i_dont_know = struct.unpack(msg_format, packet)
        if chunk_number >= 0:
            self.received_chunks += 1
            chunk = list(struct.unpack(self.packet_format, packet))
            #stderr.write(f" ->{packet} {chunk}<-")
            chunk[ChunkStructure.ORIGIN_ADDR] = IP_tools.int2ip(chunk[ChunkStructure.ORIGIN_ADDR])
            chunk[ChunkStructure.HOPS] += 1
            transmission_time = time.time() - chunk[ChunkStructure.TIME]
            #chunk[ChunkStructure.TIME] = transmission_time
            stderr.write(f" <-{transmission_time}->")
            #stderr.write(f" {transmission_time:.2}")
            self.lg.debug(f"{self.ext_id}: transmission time={transmission_time}")
            self.lg.debug(f"{self.ext_id}: received chunk {chunk} from {sender}")
            self.process_chunk(chunk, sender)
            self.send_chunks_to_the_next_neighbor()
        else:
            if chunk_number == Messages.HELLO:
                self.process_hello(sender)
            elif chunk_number == Messages.GOODBYE:
                self.process_goodbye(sender)
            else:
                stderr.write(f"{self.ext_id}: unexpected control chunk with code={chunk_number}")
        return (chunk_number, sender)            
