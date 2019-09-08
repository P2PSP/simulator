"""
@package simulator
monitor_dbs module
"""

import struct

from .messages import Messages
from .peer_dbs import Peer_DBS
from .socket_wrapper import Socket_wrapper as socket

class Monitor_DBS(Peer_DBS):
    def __init__(self, id, name, loglevel):
        #self.losses = 0
        super().__init__(id, name, loglevel)

    def complain(self, chunk_number):
        msg = struct.pack("!ii", Messages.LOST_CHUNK, chunk_number)
        self.team_socket.sendto(msg, self.splitter)
        self.lg.info("{}: [lost chunk {}] complain sent to splitter {}".format(self.id, chunk_number, self.splitter))

    # def request_chunk(self, chunk_number, peer):
    #    Peer_DBS.request_chunk(self, chunk_number, peer) # super()?
    #    self.complain(chunk_number)
