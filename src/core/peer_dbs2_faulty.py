"""
@package simulator
peer_dbs2_faulty module
"""

# Instantiable class. Only for the simulator.

from .peer_dbs2_simulator import Peer_DBS2_simulator

class Peer_DBS2_faulty(Peer_DBS2_simulator):

    def __init__(self, id, name = "Peer_DBS2_faulty"):
        Peer_DBS2_simulator.__init__(self, id, name)
        self.lg.debug("Faulty peer instantiated")

    def choose_target(self):
        self.target = self.forward[self.public_endpoint][0]  # The first peer in the list (possiblely random)
        self.lg.debug(f"{self.ext_id}: selected target {self.target}")

    def send_chunks_to_neighbors(self):
        self.lg.debug(f"{self.ext_id}: sending chunks to neighbors (pending={self.pending})")
        # Select next entry in pending with chunks to send
        if len(self.pending) > 0:
            counter = 0
            neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
            if neighbor == self.target:
                pass
            else:
                self.send_chunks(neighbor)
            while len(self.pending[neighbor]) == 0:
                self.neighbor_index = list(self.pending.keys()).index(neighbor) + 1
                neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
                counter += 1
                if counter > len(self.pending):
                    break

