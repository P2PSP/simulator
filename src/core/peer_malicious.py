"""
@package simulator
peer_malicious module
"""
from queue import Queue
from threading import Thread
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .peer_strpeds import Peer_STRPEDS
import time
import random

class Peer_Malicious(Peer_STRPEDS):
    
    def __init__(self,id):
        super().__init__(id)
        self.MPTR = 5
        self.chunks_sent_to_main_target = 0
        self.persistent_attack = True
        self.attacked_count = 0
        sim.SHARED_LIST["malicious"].append(self.id)
        print("Peer Malicious initialized")

    def connect_to_the_splitter(self):
        hello = (-1,"MP")
        self.connect(hello, self.splitter)
        
    def receive_the_list_of_peers(self):
        Peer_STRPEDS.receive_the_list_of_peers(self)
        self.first_main_target()
        
    def first_main_target(self):
        self.main_target = self.choose_main_target()

    def choose_main_target(self):
        target = None
        
        if self.attacked_count < (len(self.peer_list)//2):
            malicious_list = sim.SHARED_LIST["malicious"]
            attacked_list = sim.SHARED_LIST["attacked"]
            #import ipdb;ipdb.set_trace()
            availables = list(set(self.peer_list)-set(attacked_list)-set(malicious_list))

            if availables:
                target = random.choice(availables)
                sim.SHARED_LIST["attacked"].append(target)
                if __debug__:
                    print("Main target selected:",target)
                
                self.chunks_sent_to_main_target = 0
                self.attacked_count += 1
        
        return target

    def all_attack(self):
        if __debug__:
            print("All attack mode")

        sim.SHARED_LIST["regular"].append(self.main_target)

    def get_poisoned_chunk(self, chunk):
        return (chunk[0],"B")
        
    def send_chunk(self, peer):
        poisoned_chunk = self.get_poisoned_chunk(self.receive_and_feed_previous)
        
        if self.persistent_attack:
            if peer == self.main_target:
                if self.chunks_sent_to_main_target < self.MPTR:
                    self.sendto(poisoned_chunk, peer)
                    self.sendto_counter += 1
                    self.chunks_sent_to_main_target += 1
                    if __debug__:
                        print("Attacking Main target", self.main_target, "attack", self.chunks_sent_to_main_target)
                else:
                    self.all_attack()
                    self.sendto(poisoned_chunk, peer)
                    self.sendto_counter += 1
                    self.main_target = self.choose_main_target()
                    if __debug__:
                        print("Attacking Main target", peer, ". Replaced by", self.main_target)
            else:
                if peer in sim.SHARED_LIST["regular"]:
                    self.sendto(poisoned_chunk, peer)
                    self.sendto_counter += 1
                    if __debug__:
                        print("All Attack:",peer)
                else:
                    self.sendto(self.receive_and_feed_previous, peer)
                    self.sendto_counter += 1
                    if __debug__:
                        print("No attack", peer)

            if self.main_target == None:
                self.main_target = self.choose_main_target()

        #TO-DO: on-off and selective attacks
        else:
            self.sendto(self.receive_and_feed_previous, peer)
            self.sendto_counter += 1

    
