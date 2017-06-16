"""
@package simulator
peer_sss module
"""
from queue import Queue
from threading import Thread
from .common import Common
from .peer_strpeds import Peer_STRPEDS
import time

class Peer_SSS(Peer_STRPEDS):
    
    def __init__(self,id):
        super().__init__(id)
        
        #--------- For simulation purposes only ------------
        # To do shamir secret sharing instead of using this
        self.previous_t = -1
        self.current_t = 0
        self.splitter_t = -1
        self.previous_round = -1
        #---------------------------------------------------

        print("Peer SSS initialized")

    def get_my_secret_key(self, shares):
        #Not needed for simulation
        return NotImplementedError

    def process_message(self, message, sender):

        if sender in self.bad_peers:
            if __debug__:
                print(self.id,"Sender is  in the bad peer list", sender)
            return -1

        if sender == self.splitter["id"] or self.check_message(message, sender):
            if self.is_a_control_message(message) and message[1] == "S":
                return self.handle_bad_peers_request()
            else:
                if self.is_a_control_message(message):
                    return Peer_STRPEDS.process_message(self, message, sender)
                else:
                    if self.previous_round == message[2]: #current round
                        self.current_t += 1
                        if self.previous_t >= self.splitter_t:
                            return Peer_STRPEDS.process_message(self, message, sender)
                        else:
                            encrypted_message = (message[0],"B")
                            return Peer_STRPEDS.process_message(self, encrypted_message, sender)
                    elif self.previous_round != message[2]: #change of round
                        if self.previous_round == -1:
                            self.splitter_t = 0
                        else:
                            self.splitter_t = message[3]
                            
                        self.previous_round = message[2]
                        self.previous_t = self.current_t
                        self.current_t = 1
                        return Peer_STRPEDS.process_message(self, message, sender)
        else:
            self.process_bad_message(message, sender)
            return self.handle_bad_peers_request()

        return -1

    
