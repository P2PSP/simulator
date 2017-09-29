"""
@package simulator
peer_malicious_sss module
"""
from .simulator_stuff import Simulator_stuff as sim
from .peer_sss import Peer_SSS
import random


class Peer_Malicious_SSS(Peer_SSS):

    def __init__(self, id):
        super().__init__(id)
        self.MPTR = 5
        self.chunks_sent_to_main_target = 0
        self.persistent_attack = True
        self.attacked_count = 0
        sim.SHARED_LIST["malicious"].append(self.id)
        print("Peer Malicious SSS initialized")

    def receive_the_list_of_peers(self):
        Peer_SSS.receive_the_list_of_peers(self)
        self.first_main_target()

    def first_main_target(self):
        self.main_target = self.choose_main_target()

    def choose_main_target(self):
        target = None
        if self.attacked_count < (len(self.peer_list)//2):
            malicious_list = sim.SHARED_LIST["malicious"]
            attacked_list = sim.SHARED_LIST["attacked"]
            availables = list(set(self.peer_list)-set(attacked_list)-set(malicious_list))

            if availables:
                target = random.choice(availables)
                sim.SHARED_LIST["attacked"].append(target)
                if __debug__:
                    print("Main target selected:", target)

                self.chunks_sent_to_main_target = 0
                self.attacked_count += 1

        return target

    def all_attack(self):
        if __debug__:
            print("All attack mode")

        sim.SHARED_LIST["regular"].append(self.main_target)

    def get_poisoned_chunk(self, chunk):
        return (chunk[0], "B", chunk[2], chunk[3])

    def send_chunk(self, peer):
        encrypted_chunk = (self.receive_and_feed_previous[0], "B", self.receive_and_feed_previous[2], self.receive_and_feed_previous[3])
        current_round = self.receive_and_feed_previous[2]
        if ((current_round-1) in self.t) and (self.first_round != (current_round-1)):
            if self.t[(current_round-1)] >= self.splitter_t[(current_round-1)]:
                self.send_chunk_attack(peer)
            else:
                print("###########=================>>>>", self.id, "Need more shares, I had", self.t[(current_round-1)], "from", self.splitter_t[(current_round-1)], "needed")
                self.team_socket.sendto(encrypted_chunk, peer)
                self.sendto_counter += 1
        else:
            if (current_round-1) == self.first_round:
                print(self.id, "I cant get enough shares in my first round")
            else:
                print(self.id, "is my first round")
                self.first_round = current_round
            self.send_chunk_attack(peer)

    def send_chunk_attack(self, peer):
        poisoned_chunk = self.get_poisoned_chunk(self.receive_and_feed_previous)

        if self.persistent_attack:
            if peer == self.main_target:
                if self.chunks_sent_to_main_target < self.MPTR:
                    self.team_socket.sendto(poisoned_chunk, peer)
                    self.sendto_counter += 1
                    self.chunks_sent_to_main_target += 1
                    #if __debug__:
                        #print("Attacking Main target", self.main_target, "attack", self.chunks_sent_to_main_target)
                else:
                    self.all_attack()
                    self.team_socket.sendto(poisoned_chunk, peer)
                    self.sendto_counter += 1
                    self.main_target = self.choose_main_target()
                    #if __debug__:
                       # print("Attacking Main target", peer, ". Replaced by", self.main_target)
            else:
                if peer in sim.SHARED_LIST["regular"]:
                    self.team_socket.sendto(poisoned_chunk, peer)
                    self.sendto_counter += 1
                    #if __debug__:
                        #print("All Attack:", peer)
                else:
                    self.team_socket.sendto(self.receive_and_feed_previous, peer)
                    self.sendto_counter += 1
                    #if __debug__:
                        #print("No attack", peer)

            if self.main_target is None:
                self.main_target = self.choose_main_target()

        #TO-DO: on-off and selective attacks
        else:
            self.team_socket.sendto(self.receive_and_feed_previous, peer)
            self.sendto_counter += 1
