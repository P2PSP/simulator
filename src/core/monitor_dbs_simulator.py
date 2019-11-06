"""
@package simulator
monitor_dbs_simulator module
"""

from .monitor_dbs import Monitor_DBS
from .peer_dbs_simulator import Peer_DBS_simulator

class Monitor_DBS_simulator(Monitor_DBS, Peer_DBS_simulator):

    def receive_the_chunk_size(self):
        Peer_DBS_simulator.receive_the_chunk_size(self)

    def set_packet_format(self):
        Peer_DBS_simulator.set_packet_format(self)
        
    def compose_message(self, chunk_number):
        return Peer_DBS_simulator.compose_message(self, chunk_number)

    def unpack_chunk(self, packet):
        return Peer_DBS_simulator.unpack_chunk(self, packet)

    def clear_entry_in_buffer(self, buffer_box):
        return Peer_DBS_simulator.clear_entry_in_buffer(self, buffer_box)

    def empty_entry_in_buffer(self):
        return Peer_DBS_simulator.empty_entry_in_buffer(self)

#    def set_min_activiy(self, min_activity):
#        return Peer_DBS_simulator.set_min_activiy(min_activity)
