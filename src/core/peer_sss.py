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
                        if self.t[(current_round-1)] >= self.splitter_t[(current_round-1)]:
                            return Peer_STRPEDS.process_message(self, message, sender)
                        else:
                            print(self.id, "Need more shares, I had", self.t[(current_round-1)], "from", self.splitter_t[(current_round-1)], "needed")
                            encrypted_message = (message[0],"B")
                            return Peer_STRPEDS.process_message(self, encrypted_message, sender)
                    else:
                        print(self.id, "is my first round")
                        return Peer_STRPEDS.process_message(self, message, sender)
                        
                    '''
                    print("Current Round", message[2], "Previous Round", self.previous_round)
                    if self.previous_round == message[2]: #current round
                        self.current_t += 1
                        print(self.id, "from", self.previous_t ,"to", self.current_t)
                        if self.previous_t >= self.splitter_previous_t:
                            return Peer_STRPEDS.process_message(self, message, sender)
                        else:
                            print(self.id, "Need more shares, I had", self.previous_t, "from", self.splitter_previous_t, "needed")
                            encrypted_message = (message[0],"B")
                            return Peer_STRPEDS.process_message(self, encrypted_message, sender)
                    elif self.previous_round != message[2]: #change of round
                        if self.previous_round == -1:
                            self.splitter_previous_t = 0
                            self.splitter_current_t = message[3]
                        else:
                            self.splitter_previous_t = self.splitter_current_t
                            self.splitter_current_t = message[3]
                            
                        self.previous_round = message[2]
                        self.previous_t = self.current_t
                        self.current_t = 1
                        print(self.id, "from", self.previous_t ,"to", self.current_t)
                        return Peer_STRPEDS.process_message(self, message, sender)
                    '''
        else:
            self.process_bad_message(message, sender)
            return self.handle_bad_peers_request()

        return -1

    
