"""
@package simulator
peer_dbs2_faulty module
"""

# Instantiable class. Only for the simulator.

from .peer_dbs2 import Peer_DBS2

class Peer_DBS2_Faulty(Peer_DBS2):

    def __init__(self):
        Peer_DBS2.__init__(self)
        self.lg.debug("Faulty peer instantiated")

    def choose_target(self):
        target = self.forward[self.public_endpoint][0] # The first monitor
        self.lg.debug(f"{self.ext_id}: selected target {target}")
        return target

    def send_chunks_to_neighbors(self):
        self.lg.debug(f"{self.ext_id}: sending chunks to neighbors (pending={self.pending})")
        # Select next entry in pending with chunks to send
        if len(self.pending) > 0:
            counter = 0
            neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
            if neighbor == self.target:
                self.send_chunks((self.public_endpoint, 65535))
            else:
                self.send_chunks(neighbor)
            while len(self.pending[neighbor]) == 0:
                self.neighbor_index = list(self.pending.keys()).index(neighbor) + 1
                neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
                counter += 1
                if counter > len(self.pending):
                    break

