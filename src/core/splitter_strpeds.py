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
        print("Splitter STRPEDS initialized")
        

    def send_dsa_key(self):
        #is it needed?
        return NotImplementedError

    def gather_bad_peers(self):

    def get_peer_for_gathering(self):

    def get_trusted_peer_for_gathering(self):

    def request_bad_peers(self, dest):

    def init_key(self):
        return NotImplementedError

    def get_message(self, chunk_number, chunk, dst):

    def add_trusted_peer(self, peer):

    def process_bad_peers_message(self,message, sender):

    def handle_bad_peer_from_trusted(self, bad_peer, sender):

    def handle_bad_peer_from_regular(self, bad_peer, sender):

    def punish_peer(self, peer, message):

    def on_round_beginning(self):

    def refresh_TPs(self):

    def punish_peers(self):

    def punish_TPs(self):

    
