"""
@package simulator
monitor_dbs module
"""

import struct

from .messages import Messages
from .peer_dbs import Peer_DBS
from .socket_wrapper import Socket_wrapper as socket

class Monitor_DBS(Peer_DBS):

    def complain(self, chunk_number):
        msg = struct.pack("!ii", Messages.LOST_CHUNK, chunk_number)
        self.team_socket.sendto(msg, self.splitter)
        self.lg.debug(f"{self.ext_id}: [lost chunk {chunk_number}] sent to the splitter {self.splitter}")

    # def request_chunk(self, chunk_number, peer):
    #    Peer_DBS.request_chunk(self, chunk_number, peer) # super()?
    #    self.complain(chunk_number)
