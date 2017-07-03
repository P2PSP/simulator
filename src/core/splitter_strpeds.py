"""
@package p2psp-simulator
splitter_strpeds module
"""
from queue import Queue
from threading import Thread
from .splitter_dbs import Splitter_DBS
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
import time
import random

class Splitter_STRPEDS(Splitter_DBS):
    
    def __init__(self):
        super().__init__()
        self.trusted_peers = []
        self.bad_peers = []
        self.trusted_peers_discovered = []
        self.complaints = {}
        self.p_mpl = 1
        self.p_tpl = 1
        
        #--- Only for simulation purposes ---
        self.number_of_malicious = 0
        #------------------------------------

        print("Splitter STRPEDS initialized")
        

    def send_dsa_key(self):
        #Not needed for simulation
        return NotImplementedError

    def gather_bad_peers(self):
        for p in self.peer_list:
            sim.UDP_SOCKETS[p].put(self.id,(-1,"S"))

    def init_key(self):
        #Not needed for simulation
        return NotImplementedError

    def handle_a_peer_arrival(self):
        content = self.recv()
        message = content[0]
        incoming_peer = content[1]
        print(self.id,"acepted connection from peer", incoming_peer)
        print(self.id, "message", content)
        if (message[1] == "M"):
            self.number_of_monitors += 1
            self.trusted_peers.append(incoming_peer)
            
        #---- Only for simulation purposes. Unknown in real implementation -----
        if (message[1] == "MP"):
            self.number_of_malicious += 1
        #-----------------------------------------------------------------------
        
        print("NUMBER OF MONITORS", self.number_of_monitors)

        self.send_buffer_size(incoming_peer)
        self.send_the_number_of_peers(incoming_peer)
        self.send_the_list_of_peers(incoming_peer)

        print(self.id, ": waiting for outgoing peer")
        (m, x) = self.recv()
        print(self.id, ": received", m, "from", x)
            
        self.insert_peer(incoming_peer)
        sim.SIMULATOR_FEEDBACK["DRAW"].put(("O","Node","IN",incoming_peer))
    
    def process_bad_peers_message(self, message, sender):
        bad_list = message[2]
        for bad_peer in bad_list:
            if sender in self.trusted_peers:
                self.handle_bad_peer_from_trusted(bad_peer, sender)
            else:
                self.handle_bad_peer_from_regular(bad_peer, sender)

    def handle_bad_peer_from_trusted(self, bad_peer, sender):
        self.add_complaint(bad_peer, sender)
        if bad_peer not in self.bad_peers:
            self.bad_peers.append(bad_peer)

    def handle_bad_peer_from_regular(self, bad_peer, sender):
        self.add_complaint(bad_peer, sender)
        complaint_ratio = len(self.complaints[bad_peer])/len(self.peer_list)
        if complaint_ratio >= self.majority_ratio:
            self.punish_peer(bad_peer, "by majority decision")

    def add_complaint(self, bad_peer, sender):
        self.complaints.setdefault(bad_peer,[]).append(sender)
            
    def punish_peer(self, peer, message):
        if peer in self.peer_list:
            self.remove_peer(peer)
            if __debug__:
                print("bad peer", peer, message)

    def on_round_beginning(self):
        self.punish_peers()
        #self.punish_TPs()

    def punish_peers(self):
        for b in self.bad_peers:
            r = random.randint(0,1)
            if r <= self.p_mpl:
                self.punish_peer(b, "by trusted")
                self.bad_peers.remove(b)
                
                #--- Only for simulation purposes ---
                self.number_of_malicious -= 1
                #------------------------------------

    def punish_TPs(self):
        for tp in self.trusted_peers_discovered:
            r = random.randint(0,1)
            if r <= self.p_tpl:
                self.punish_peer(tp, "by splitter")
                self.trusted_peers_discovered.remove(tp)

    def increment_unsupportivity_of_peer(self, peer):
        try:
            if peer not in self.trusted_peers:
                self.losses[peer] += 1
        except KeyError:
            print("The unsupportive peer", peer, "does not exist!")
        else:
            print(peer, "has loss", self.losses[peer], "chunks")
            if self.losses[peer] > Common.MAX_CHUNK_LOSS:
                if peer not in self.bad_peers:
                    print(peer, 'removed')
                    self.bad_peers.append(peer)
        finally:
           pass

    def moderate_the_team(self):
        while self.alive:
            message = self.recvfrom()
            action = message[0]
            sender = message[1]

            if (sender == "SIM"):
                if (action[1] == "K"):
                    sim.SIMULATOR_FEEDBACK["DRAW"].put(("Bye","Bye"))
                    self.alive = False
            else:
                if action[1] == "L":
                    lost_chunk_number = self.get_lost_chunk_number(action)
                    self.process_lost_chunk(lost_chunk_number, sender)

                elif action[1] == "S":
                    if __debug__:
                        print("Bad complaint received")
                    if sender in self.trusted_peers:
                        if __debug__:
                            print("Complaint about bad peers from", sender)
                        self.trusted_peers_discovered.append(sender)
                        self.process_bad_peers_message(action, sender)
                    
                else:
                    self.process_goodbye(sender)

    def run(self):
        Thread(target=self.handle_arrivals).start()
        Thread(target=self.moderate_the_team).start()
        Thread(target=self.reset_counters_thread).start()

        while self.alive:
            chunk = self.receive_chunk()
            try:
                peer = self.peer_list[self.peer_number]
                message = (self.chunk_number, chunk, self.current_round)
                
                self.send_chunk(message, peer)

                self.destination_of_chunk.insert(self.chunk_number % self.buffer_size, peer)
                self.chunk_number = (self.chunk_number + 1) % Common.MAX_CHUNK_NUMBER                
                self.compute_next_peer_number(peer)
            except IndexError:
                print("The monitor peer has died!")

            if self.peer_number == 0:

                self.on_round_beginning()
                
                sim.SIMULATOR_FEEDBACK["STATUS"].put(("R", self.current_round))
                sim.SIMULATOR_FEEDBACK["DRAW"].put(("R", self.current_round))
                sim.SIMULATOR_FEEDBACK["DRAW"].put(("T","M",self.number_of_monitors, self.current_round))
                sim.SIMULATOR_FEEDBACK["DRAW"].put(("T","P",(len(self.peer_list)-self.number_of_monitors), self.current_round))
                sim.SIMULATOR_FEEDBACK["DRAW"].put(("T","MP",self.number_of_malicious, self.current_round))

                self.current_round += 1
                
                for peer in self.outgoing_peer_list:
                    self.say_goodbye(peer)
                    self.remove_peer(peer)

                del self.outgoing_peer_list[:]
