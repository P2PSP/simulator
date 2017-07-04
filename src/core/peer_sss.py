"""
@package simulator
peer_sss module
"""
from queue import Queue
from threading import Thread
from .peer_strpeds import Peer_STRPEDS
import time, sys

class Peer_SSS(Peer_STRPEDS):
    
    def __init__(self,id):
        super().__init__(id)
        
        #--------- For simulation purposes only ------------
        # To do shamir secret sharing instead of using this
        self.t = {}
        self.splitter_t = {}
        #---------------------------------------------------

        print("Peer SSS initialized")

    def get_my_secret_key(self, shares):
        #Not needed for simulation
        return NotImplementedError

    def process_message(self, message, sender):

        if sender in self.bad_peers:
            if __debug__:
                print(self.id,"Sender is in the bad peer list", sender)
            return -1

        if sender == self.splitter or self.check_message(message, sender):
            if self.is_a_control_message(message) and message[1] == "S":
                return self.handle_bad_peers_request()
            else:
                if self.is_a_control_message(message):
                    return Peer_STRPEDS.process_message(self, message, sender)
                else:
                    current_round = message[2]
                    if (current_round in self.t):
                        self.t[current_round] += 1
                    else:
                        self.t[current_round] = 1

                    self.splitter_t[current_round] = message[3]              

                    print(self.id, "current_round", current_round)

                    if ((current_round-1) in self.t):
                        print(self.id, "t", self.t[(current_round-1)], "splitter_t", self.splitter_t[(current_round-1)])
                        print(self.id, "this.t", self.t[(current_round)], "this.splitter_t", self.splitter_t[(current_round)])

                    return Peer_STRPEDS.process_message(self, message, sender)
                        
        else:
            self.process_bad_message(message, sender)
            return self.handle_bad_peers_request()

        return -1

    def send_chunk(self, peer):
        encrypted_chunk = (self.receive_and_feed_previous[0],"B")
        current_round = self.receive_and_feed_previous[2]
        if ((current_round-1) in self.t):
            if self.t[(current_round-1)] >= self.splitter_t[(current_round-1)]:
                self.sendto(self.receive_and_feed_previous, peer)
                self.sendto_counter += 1
            else:
                print("###########=================>>>>", self.id, "Need more shares, I had", self.t[(current_round-1)], "from", self.splitter_t[(current_round-1)], "needed")
                self.sendto(encrypted_chunk, peer)
                self.sendto_counter += 1
        else:
            print(self.id, "is my first round")
            self.sendto(self.receive_and_feed_previous, peer)    
