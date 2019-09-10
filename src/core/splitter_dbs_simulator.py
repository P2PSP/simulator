"""
@package p2psp-simulator
splitter_dbs_simulator module
"""

# Simulator specific behavior.

import struct
import sys
import time
from threading import Thread
import colorama
from core.splitter_dbs import Splitter_DBS

from .common import Common
from .simulator_stuff import Simulator_stuff
import logging
import psutil

class Splitter_DBS_simulator(Simulator_stuff, Splitter_DBS):

    def __init__(self,
                 buffer_size = 32,
                 max_chunk_loss = 16,
                 number_of_rounds = 100,
                 name = "Splitter_DBS_simulator",
                 loglevel = logging.ERROR
    ):
        super().__init__(buffer_size = buffer_size,
                         max_chunk_loss = max_chunk_loss,
                         name = name,
                         loglevel = loglevel
        )
        self.number_of_rounds = number_of_rounds
        self.lg.debug("Splitter_DBS_simulator: initialized")
        colorama.init()
        #self.total_lost_chunks = 0

    def retrieve_chunk(self):
        # Simulator_stuff.LOCK.acquire(True,0.1)
        #time.sleep(Common.CHUNK_CADENCE)  # Simulates bit-rate control
        # C -> Chunk, L -> Loss, G -> Goodbye, B -> Broken, P -> Peer, M -> Monitor, R -> Ready
        #if __debug__:
            #sys.stderr.write(str(len(self.team))); sys.stderr.flush()
        time.sleep(psutil.cpu_percent()/4000.0)
        return b'C'

    def provide_feedback(self, peer_number, chunk_number):
        if Simulator_stuff.FEEDBACK:
            Simulator_stuff.FEEDBACK["STATUS"].put(("R", self.current_round))
            Simulator_stuff.FEEDBACK["DRAW"].put(("R", self.current_round))
            #Simulator_stuff.FEEDBACK["DRAW"].put(("T", "M", self.number_of_monitors, self.current_round))
            #Simulator_stuff.FEEDBACK["DRAW"].put(("T", "P", (len(self.team) - self.number_of_monitors), self.current_round))

        if peer_number == 0:
            self.current_round += 1
            sys.stderr.write(f" {colorama.Fore.YELLOW}r{str(self.current_round)}{colorama.Style.RESET_ALL}"); sys.stderr.flush()
            #self.lg.info("round = {}".format(self.current_round))
            #sys.stderr.write(f"{self.id}: round={self.current_round:03}/{self.number_of_rounds:03} chunk_number={chunk_number:05} number_of_peers={len(self.team):03}\r")
            #print("{}: len(peers_list)={}".format(self.id, len(self.team)))
            #sys.stderr.write(str(self.current_round) + "/" + str(self.max_number_of_rounds) + " " + str(self.chunk_number) + " " + str(len(self.team)) + "\r")

    def process_lost_chunk(self, lost_chunk_number, sender):
        super().process_lost_chunk(lost_chunk_number = lost_chunk_number, sender = sender)
        sys.stderr.write(f" {colorama.Fore.RED}L{lost_chunk_number}{colorama.Style.RESET_ALL}")
        #self.total_lost_chunks += 1

    def insert_peer(self, peer):
        super().insert_peer(peer)
        sys.stderr.write(f" {colorama.Fore.GREEN}P{len(self.team)}{colorama.Style.RESET_ALL}"); sys.stderr.flush()

    def del_peer(self, peer_index):
        super().del_peer(peer_index)
        sys.stderr.write(f" {colorama.Fore.BLUE}R{peer_index}({len(self.team)}){colorama.Style.RESET_ALL}"); sys.stderr.flush()
        if __debug__:
            # S I M U L A T I O N
            if Simulator_stuff.FEEDBACK:
                Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "OUT", ','.join(map(str, peer))))
            if peer[0] == "M" and peer[1] != "P":
                self.number_of_monitors -= 1

    def run(self):
        super().run()
        sys.stderr.write("\n")
        #sys.stderr.write(f"\n{self.id}: {self.chunks_lost_by_team} lost chunks of {self.chunks_received_by_team}\n")
        if Simulator_stuff.FEEDBACK:
            Simulator_stuff.FEEDBACK["STATUS"].put(("Bye", "Bye"))
            self.lg.info(f"{self.id}: Bye sent to simulator")

    def is_alive(self):
        if self.current_round <= self.number_of_rounds:
            self.alive = True
        else:
            self.alive = False
