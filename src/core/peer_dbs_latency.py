"""
@package simulator
peer_dbs module
"""

# DBS (Data Broadcasting Set) layer

# DBS peers receive chunks from the splitter and other peers, and
# resend them, depending on the forwarding requests performed by the
# peers. In a nutshell, if a peer X wants to receive from peer Y
# the chunks from origin Z, X must request it to Y, explicitally.

import time
import struct
import logging
import random
from threading import Thread
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import Simulator_socket as socket
from .simulator_stuff import hash
from .peer_dbs import Peer_DBS

class Peer_DBS_latency(Peer_DBS):

    CHUNK_TIME = 4

    def __init__(self, id, name):
        super().__init__(id, name)        
        self.max_pkg_length = struct.calcsize("islif")
        
    def process_message(self):
        try:
            pkg, sender = self.receive_packet()
            print("{} {}".format(len(pkg), self.max_pkg_length))
            # self.lg.debug("{}: received {} from {} with length {}".format(self,id, pkg, sender, len(pkg)))
            if len(pkg) == self.max_pkg_length:
                message = struct.unpack("islif", pkg)
                # Data message: [chunk number, chunk, origin, (address and port), time stamp]
                message = message[self.CHUNK_NUMBER], \
                          message[self.CHUNK_DATA], \
                          (socket.int2ip(message[self.ORIGIN]),message[self.ORIGIN+1]), \
                          message[self.CHUNK_TIME]
            elif len(pkg) == struct.calcsize("iii"):
                message = struct.unpack("iii", pkg)  # Control message:
                                                     # [control, parameter]
            elif len(pkg) == struct.calcsize("ii"):
                message = struct.unpack("ii", pkg)  # Control message:
                                                    # [control, parameter]
            else:
                message = struct.unpack("i", pkg)  # Control message:
                                                   # [control]
            return self.process_unpacked_message(message, sender)
        except self.team_socket.timeout:
            #self.say_goodbye(self.splitter)
            #self.say_goodbye_to_the_team()
            raise
        #    return (0, self.id)

    def compose_message(self, chunk_number):
        chunk_position = chunk_number % self.buffer_size
        chunk = self.chunks[chunk_position]
        stored_chunk_number = chunk[self.CHUNK_NUMBER]
        chunk_data = chunk[self.CHUNK_DATA]
        chunk_origin_IP = chunk[self.ORIGIN][0]
        chunk_origin_port = chunk[self.ORIGIN][1]
        time_stamp = chunk[self.CHUNK_TIME]
        message = (stored_chunk_number, chunk_data, socket.ip2int(chunk_origin_IP), chunk_origin_port, time_stamp)
        packet = struct.pack("islif", *message)
        return packet
