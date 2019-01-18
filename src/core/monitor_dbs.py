"""
@package simulator
monitor_dbs module
"""

import struct

from .common import Common
from .peer_dbs import Peer_DBS
from .simulator_stuff import Simulator_socket as socket


class Monitor_DBS(Peer_DBS):
    def __init__(self, id, name, loglevel):
        #self.losses = 0
        super().__init__(id, name, loglevel)

    def complain(self, chunk_number):
        msg = struct.pack("!ii", Common.LOST_CHUNK, chunk_number)
        self.team_socket.sendto(msg, self.splitter)
        self.lg.info("{}: [lost chunk {}] sent to {}".format(self.id, chunk_number, self.splitter))

    # def request_chunk(self, chunk_number, peer):
    #    Peer_DBS.request_chunk(self, chunk_number, peer) # super()?
    #    self.complain(chunk_number)
