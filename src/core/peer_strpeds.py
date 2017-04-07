"""
@package simulator
peer_strpeds module
"""
from queue import Queue
from threading import Thread
from .common import Common
from .peer_dbs import Peer_DBS
import time

class Peer_STRPEDS(Peer_DBS):
    
    def __init__(self,id):
        super().__init__(id)
        self.bad_peers = []
        self.losses = 0
        self.played = 0
        print("Peer STRPEDS initialized")

    def receive_dsa_key(self):
        #Not needed for simulation
        return NotImplementedError

    def process_bad_message(self, message, sender):
        self.bad_peers.append(sender)
        self.peer_list.remove(sender)
        Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge","OUT",self.id,sender))

    def is_a_control_message(self, message):
        if message[0] == -1:
            return True
        else:
            return False

    def check_message(self, message, sender):
        if sender in self.bad_peers:
            if __debug__:
                print(self.id,"Sender is in bad peer list:",sender) 
            return false

        if not self.is_a_control_message(message):
            if message[1] == "C":
                return True
            else: #(L)ost or (B)roken
                return False
        else:
            if __debug__:
                print("Sender sent a control message", message)
            return True

    def handle_bad_peers_request(self):
        self.splitter["socketUDP"].put((self.id, (-1,"S",self.bad_peers)))
        
        if __debug__:
            print("Bad peers sent to the Splitter")

        return -1

    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number%self.buffer_size][1] == "C":
            self.played +=1
        else:
            self.losses += 1
            
        self.number_of_chunks_consumed += 1
        return self.player_alive

    def process_message(self, message, sender):

        if sender in self.bad_peers:
            if __debug__:
                print(self.id,"Sender is  in the bad peer list", sender)
            return -1

        # ----- Check if new round for peer -------
        if not self.is_a_control_message(message) and sender == self.splitter["id"]:
            if self.played > 0 and self.played >= len(self.peer_list):
                clr = self.losses/self.played
                Common.SIMULATOR_FEEDBACK["DRAW"].put(("CLR",self.id,clr))
                self.losses = 0
                self.played = 0
        # ------------

        if sender == self.splitter["id"] or self.check_message(message, sender):
            if self.is_a_control_message(message) and message[1] == "S":
                return self.handle_bad_peers_request()
            else:
                return Peer_DBS.process_message(self, message, sender)
        else:
            self.process_bad_message(message, sender)
            return self.handle_bad_peers_request()

        return -1

    
