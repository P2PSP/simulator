"""
@package simulator
monitor_dbs_simulator module
"""

from .monitor_dbs import Monitor_DBS
from .peer_dbs_simulator import Peer_DBS_simulator

class Monitor_DBS_simulator(Monitor_DBS, Peer_DBS_simulator):

    def play_chunk(self, chunk_number):
        Monitor_DBS.play_chunk(self, chunk_number)

    def process_unpacked_message(self, message, sender):
        return Peer_DBS_simulator.process_unpacked_message(self, message, sender)
