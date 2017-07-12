"""
@package p2psp-simulator
splitter_sss module
"""
from queue import Queue
from threading import Thread
from .splitter_strpeds import Splitter_STRPEDS
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
import time
import random

class Splitter_SSS(Splitter_STRPEDS):
    
    def __init__(self):
        super().__init__()
        self.t = (len(self.peer_list) // 2) + 1
        print("Splitter SSS initialized")
        
    def generate_secret_key(self, peer, r):
        #Not needed for simulation
        return NotImplementedError

    def generate_shares(self, secret_key, n):
        #Not needed for simulation
        return NotImplementedError

    def remove_outgoing_peers(self):
        for p in self.outgoing_peer_list:
            self.say_goodbye(p)
            self.remove_peer(p)
        del self.outgoing_peer_list[:]

    def on_round_beginning(self):
        self.remove_outgoing_peers()
        self.punish_peers()
        self.t = (len(self.peer_list) // 2) + 1
        #For each peer in this round:
        #   self.generate_secret_key()
        #   self.generate_shares()

    def receive_chunk(self):
        time.sleep(0.08)  # bit-rate control
        #C->Chunk, L->Lost, G->Goodbye, B->Broken, P->Peer, M->Monitor, R-> Ready
        return "C"
        
    def run(self):
        Thread(target=self.handle_arrivals).start()
        Thread(target=self.moderate_the_team).start()
        Thread(target=self.reset_counters_thread).start()

        while self.alive:
            chunk = self.receive_chunk()
            try:
                peer = self.peer_list[self.peer_number]
                message = (self.chunk_number, chunk, self.current_round, self.t)
                
                self.send_chunk(message, peer)

                self.destination_of_chunk.insert(self.chunk_number % self.buffer_size, peer)
                self.chunk_number = (self.chunk_number + 1) % Common.MAX_CHUNK_NUMBER                
                self.compute_next_peer_number(peer)
                print("------> Next Peer Number ----->", self.peer_number)
            except IndexError:
                print("The monitor peer has died!")

            if self.peer_number == 0:

                self.on_round_beginning()
                
                sim.FEEDBACK["STATUS"].put(("R", self.current_round))
                sim.FEEDBACK["DRAW"].put(("R", self.current_round))
                sim.FEEDBACK["DRAW"].put(("T", "M", self.number_of_monitors, self.current_round))
                sim.FEEDBACK["DRAW"].put(("T", "P", (len(self.peer_list)-self.number_of_monitors), self.current_round))
                sim.FEEDBACK["DRAW"].put(("T", "MP", self.number_of_malicious, self.current_round))

                self.current_round += 1
        sim.FEEDBACK["STATUS"].put(("Bye", "Bye"))
        print("Splitter killed")
        exit()
