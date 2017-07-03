"""
@package simulator
peer_strpeds module
"""
from queue import Queue
from threading import Thread
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .peer_dbs import Peer_DBS
import time

class Peer_STRPEDS(Peer_DBS):
    
    def __init__(self,id):
        super().__init__(id)
        self.bad_peers = []
        print("Peer STRPEDS initialized")

    def receive_dsa_key(self):
        #Not needed for simulation
        return NotImplementedError

    def process_bad_message(self, message, sender):
        self.bad_peers.append(sender)
        self.peer_list.remove(sender)
        sim.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge","OUT",self.id,sender))

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
        #self.splitter["socketUDP"].put((self.id, (-1,"S",self.bad_peers)))
        self.sendto((-1,"S",self.bad_peers), self.splitter)
        if __debug__:
            print(self.id, "Bad peers sent to the Splitter", self.bad_peers)
        return -1

    def process_message(self, message, sender):

        if sender in self.bad_peers:
            if __debug__:
                print(self.id,"Sender is  in the bad peer list", sender)
            return -1

        if sender == self.splitter or self.check_message(message, sender):
            if self.is_a_control_message(message) and message[1] == "S":
                return self.handle_bad_peers_request()
            else:
                return Peer_DBS.process_message(self, message, sender)
        else:
            self.process_bad_message(message, sender)
            return self.handle_bad_peers_request()

        return -1

    
