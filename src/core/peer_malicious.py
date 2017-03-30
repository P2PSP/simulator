"""
@package simulator
peer_malicious module
"""
from queue import Queue
from threading import Thread
from .common import Common
from .peer_strpeds import Peer_STRPEDS
import time
import random

class Peer_Malicious(Peer_STRPEDS):
    
    def __init__(self,id):
        super().__init__(id)
        self.MPTR = 5
        self.chunks_sent_to_main_target = 0
        print("Peer STRPEDS initialized")

    def receive_the_list_of_peers(self):
        PeerDBS.receive_the_list_of_peers()
        self.first_main_target()
        
    def first_main_target(self):
        self.main_target = self.choose_main_target()

    def choose_main_target(self):
        attacked_list = common.SHARED_LIST["attacked"]
        malicious_list = common.SHARED_LIST["malicious"]
        availables = list(set(attacked_list)^set(malicious_list))

        if availables:
            target = random.choice(availables)
        else:
            target = None
            
        return target

    def all_attack(self):
        if __debug__:
            print("All attack mode")
            
        common.SHARED_LIST["regular"].put(self.main_target)

    def get_poisoned_chunk(self, chunk):
        return (chunk[0],"B")
        
    def send_chunk(self, peer):
        poisoned_chunk = self.get_poisoned_chunk(self.receive_and_feed_previous)
        
        if self.persistent_attack:
            if peer == self.main_target:
                if self.chunks_sent_to_main_target < self.MPTR:
                    Common.UDP_SOCKETS[peer].put((self.id, poisoned_chunk))
                    self.sendto_counter += 1
                    self.chunks_sent_to_main_target += 1
                    if __debug__:
                        print("Attacking Main target", self.main_target, "attack", self.chunks_sent_to_main_target)
                else:
                    self.all_attack()
                    Common.UDP_SOCKETS[peer].put((self.id, poisoned_chunk))
                    self.sendto_counter += 1
                    self.main_target = self.choose_main_target()
                    if __debug__:
                        print("Attacking Main target", peer, ". Replaced by", self.main_target)
            else:
                if peer in common.SHARED_LIST["regular"]:
                    Common.UDP_SOCKETS[peer].put((self.id, poisoned_chunk))
                    self.sendto_counter += 1
                    if __debug__:
                        print("All Attack:",peer)
                else:
                    Common.UDP_SOCKETS[peer].put((self.id, self.receive_and_feed_previous))
                    self.sendto_counter += 1
                    if __debug__:
                        print("No attack", peer)

        #TO-DO: on-off and selective attacks
        else:
            Common.UDP_SOCKETS[peer].put((self.id, self.receive_and_feed_previous))
            self.sendto_counter += 1

    
