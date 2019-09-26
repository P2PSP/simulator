"""
@package p2psp-simulator
splitter_dbs_simulator module
"""

# Simulator specific behavior. The chunks are simulated, considering
# the CPU load.

import struct
import sys
import time
from threading import Thread
from core.splitter_dbs import Splitter_DBS

from .common import Common
from .simulator_stuff import Simulator_stuff
import logging
import psutil
import colorama

class Splitter_DBS_simulator(Simulator_stuff, Splitter_DBS):

    def __init__(self,
                 buffer_size = 32,
                 max_chunk_loss = 16,
                 number_of_rounds = 100,
                 speed = 4000,
                 name = "Splitter_DBS_simulator"):
        super().__init__(buffer_size = buffer_size,
                         max_chunk_loss = max_chunk_loss)
        self.number_of_rounds = number_of_rounds
        self.speed = speed
        self.cpu_usage = 50
        self.current_round = 0
        self.lg.debug("{name}: initialized")
        colorama.init()

    def send_the_chunk_size(self, peer_serve_socket):
        pass

    def send_the_header_bytes(self, peer_serve_socket):
        pass

    def send_the_header(self, peer_serve_socket):
        pass

    def compute_cpu_usage(self):
        while True:
            self.cpu_usage = 0.1*psutil.cpu_percent() + 0.9*self.cpu_usage
            sys.stderr.write(f" {int(self.cpu_usage)}"); sys.stderr.flush()
            time.sleep(0.5)
    
    def retrieve_chunk(self):
        # Simulator_stuff.LOCK.acquire(True,0.1)
        #time.sleep(Common.CHUNK_CADENCE)  # Simulates bit-rate control
        # C -> Chunk, L -> Loss, G -> Goodbye, B -> Broken, P -> Peer, M -> Monitor, R -> Ready
        #if __debug__:
            #sys.stderr.write(str(len(self.team))); sys.stderr.flush()
        sleeping_time = self.cpu_usage/self.speed
        time.sleep(sleeping_time)
        #time.sleep(0.1)
        return b'C'

    def is_alive(self):
        if self.current_round <= self.number_of_rounds:
            self.alive = True
        else:
            self.alive = False
        Simulator_stuff.FEEDBACK["STATUS"].put(("R", self.current_round))
        Simulator_stuff.FEEDBACK["DRAW"].put(("R", self.current_round))

    def run(self):
        Thread(target=self.compute_cpu_usage).start()
        super().run()
        sys.stderr.write("\n")
        Simulator_stuff.FEEDBACK["STATUS"].put(("Bye", "Bye"))
        self.lg.debug(f"{self.id}: Bye sent to simulator")
