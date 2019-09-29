"""
@package simulator
peer_dbs_simulator module
"""

from .peer_dbs2 import Peer_DBS2
from .peer_dbs_simulator import Peer_DBS_simulator

#class Peer_DBS2_simulator(Peer_DBS2):
class Peer_DBS2_simulator(Peer_DBS2, Peer_DBS_simulator):

    def __init__(self, id, name = "Peer_DBS2_simulator"):
        Peer_DBS2.__init__(self)
        Peer_DBS_simulator.__init__(self, id, name)
        self.lg.debug(f"{name}: DBS2 simulator initialized")
    '''
    def receive_the_chunk_size(self):
        Peer_DBS_simulator.receive_the_chunk_size(self)

    def packet_format(self):
        Peer_DBS_simulator.packet_format(self)

    def compose_message(self, chunk_number):
        Peer_DBS_simulator.compose_message(self, chunk_number)

    def unpack_chunk(self, packet):
        return Peer_DBS_simulator.unpack_chunk(self, packet)

    def clear_entry_in_buffer(self, buffer_box):
        return Peer_DBS_simulator.clear_entry_in_buffer(self, buffer_box)

    def init_entry_in_buffer(self):
        return Peer_DBS_simulator.init_entry_in_buffer(self)
    '''
