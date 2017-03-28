"""
@package p2psp-simulator
splitter_dbs module
"""
from queue import Queue
from threading import Thread
from .splitter_dbs import Splitter_DBS
from .common import Common
import time

class Splitter_STRPEDS(Splitter_DBS):
    MAX_NUMBER_OF_CHUNK_LOSS = 32
    BUFFER_SIZE = 1024
    
    def __init__(self):
        super().__init__()
        self.trusted_peers = []
        self.bad_peers = []
        print("Splitter STRPEDS initialized")
        

    def send_dsa_key(self):
        #it is not needed in terms of simulation
        return NotImplementedError

    def gather_bad_peers(self):
        for p in self.peer_list:
            Common.UDP_SOCKETS[p].put(self.id,(-1,"S"))

    def init_key(self):
        #it is not needed in terms of simulation
        return NotImplementedError

    def process_bad_peers_message(self, message, sender):
        bad_list = message[1]
        for bad_peer in bad_list:
            if sender in self.trusted_peers:
                self.handle_bad_peer_from_trusted(bad_peer, sender)
            else:
                self.handle_bad_peer_from_regular(bad_peer, sender)

    def handle_bad_peer_from_trusted(self, bad_peer, sender):
        self.add_complain(bad_peer, sender)
        if bad_peer not in self.bad_peers:
            self.bad_peers.append(bad_peer)

    def handle_bad_peer_from_regular(self, bad_peer, sender):
        self.add_complain(bad_peer, sender)
        x = len(self.complains[bad_peer])/len(self.peer_list)
        if x >= self.majority_ratio:
            self.punish_peer(bad_peer)

    def punish_peer(self, peer, message):

    def on_round_beginning(self):

    def refresh_TPs(self):

    def punish_peers(self):

    def punish_TPs(self):

    
