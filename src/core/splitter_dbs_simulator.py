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
                 name = "Splitter_DBS_simulator"
    ):
        super().__init__(buffer_size = buffer_size,
                         max_chunk_loss = max_chunk_loss
        )
        logging.basicConfig(stream=sys.stdout, format="%(asctime)s.%(msecs)03d %(message)s %(levelname)-8s %(name)s %(pathname)s:%(lineno)d", datefmt="%H:%M:%S")
        self.lg = logging.getLogger(__name__)
        self.lg.setLevel(logging.ERROR)
        self.number_of_rounds = number_of_rounds
        self.lg.debug("{name}: initialized")
        colorama.init()
        #self.total_lost_chunks = 0

    def setup_peer_connection_socket(self, port=0):
        super().setup_peer_connection_socket(port = port)
        self.id = self.peer_connection_socket.getsockname()
        self.lg.info(f"{self.id}: I am the splitter")

    def send_chunk(self, chunk_number, chunk, peer):
        super().send_chunk(chunk_number = chunk_number,
                           chunk = chunk,
                           peer = peer)
        self.lg.info(f"{self.id}: chunk {chunk_number} sent to {peer}")

    def handle_arrivals__feedback(self, peer):
        self.lg.info(f"{self.id}: new connection from incoming {peer}")

    def handle_a_peer_arrival(self, connection):
        super().handle_a_peer_arrival(connection)
        serve_socket = connection[0]
        incoming_peer = connection[1]
        self.lg.info(f"{self.id}: accepted connection from peer {incoming_peer}")        

    def send_public_endpoint(self, endpoint, peer_serve_socket):
        self.lg.info(f"{self.id}: sending peer's (public) endpoint={endpoint}")
        super().send_public_endpoint(endpoint = endpoint,
                                     peer_serve_socket = peer_serve_socket)

    def send_the_number_of_peers(self, peer_serve_socket):
        self.lg.info(f"{self.id}: sending peers_list of length={len(self.team)}")
        super().send_the_number_of_peers(peer_serve_socket)

    def send_peer_index_in_team(self, peer_serve_socket, peer_index_in_team):
        self.lg.info(f"{self.id}: sending peer_index_in_team={peer_index_in_team}")
        super().send_peer_index_in_team(peer_serve_socket = peer_serve_socket,
                                        peer_index_in_team = peer_index_in_team)

    def insert_peer(self, peer):
        super().insert_peer(peer)
        self.lg.info(f"{self.id}: {peer} inserted in the team")
        sys.stderr.write(f" {colorama.Fore.GREEN}{len(self.team)}{colorama.Style.RESET_ALL}"); sys.stderr.flush()
        sys.stderr.write(f" {colorama.Fore.MAGENTA}{len(self.team)}{colorama.Style.RESET_ALL}"); sys.stderr.flush

    def increment_unsupportivity_of_peer__warning(self, peer):
        self.lg.warning(f"{self.id}: the unsupportive peer {peer} does not exist in {self.losses}")
        
    def increment_unsupportivity_of_peer(self, peer):
        sys.stderr.write(f" {colorama.Fore.RED}({self.team.index(peer)}){colorama.Style.RESET_ALL}")
        super().increment_unsupportivity_of_peer(peer)

    def process_lost_chunk(self, lost_chunk_number):
        super().process_lost_chunk(lost_chunk_number)
        sys.stderr.write(f" {colorama.Fore.RED}{lost_chunk_number}{colorama.Style.RESET_ALL}")
        #self.total_lost_chunks += 1

    def del_peer(self, peer_index):
        super().del_peer(peer_index)
        sys.stderr.write(f" {colorama.Fore.BLUE}{peer_index}({len(self.team)}){colorama.Style.RESET_ALL}"); sys.stderr.flush()
        sys.stderr.write(f" {colorama.Fore.MAGENTA}{len(self.team)}{colorama.Style.RESET_ALL}"); sys.stderr.flush

    def remove_peer__warning1(self, peer):
        self.lg.warning(f"{self.id}: the removed peer {peer} does not exist in {self.peer_list}")

    def remove_peer__warning2(self, peer):
        self.lg.warning(f"{self.id}: the removed peer {peer} does not exist in losses!")

    def process_goodbye(self, peer):
        self.lg.info(f"{self.id}: received [goodbye] from {peer}")
        super().process_goodbye(peer)

    def process_goodbye__feedback(self, peer):
        self.lg.info(f"{self.id}: {peer} marked for deletion")

    def remove_outgoing_peers__feedback(peer):
        self.lg.info(f"{self.id}: outgoing peer {p}")
        
    def remove_outgoing_peers(self):
        if __debug__:
            if len(self.outgoing_peers_list) > 0:
                sys.stderr.write(f"{self.id}: remove_outgoint_peers: len(outgoing_peers_list)={len(self.outgoing_peers_list)}\n")
        super().remove_outgoing_peers()

    def moderate_the_team__warning1(self, packed_msg, sender):
        self.lg.warning(f"{self.id}: unexpected message {packed_msg} with length={len(packed_msg)} received from {sender}")

    def moderate_the_team__warning2(self, msg, sender):
        self.lg.info(f"{self.id}: received [lost chunk {msg[1]}] from {sender}")
        
    def moderate_the_team__warning3(self, packed_msg, msg, sender):
        self.lg.warning(f"{self.id}: unexpected message {packed_msg} with length={len(packed_msg)} decoded as {msg} received from {sender}")

    def moderate_the_team__hello_feedback(self, sender):
        self.lg.info(f"{self.id}: received [hello] from {sender}")
        
    def retrieve_chunk(self):
        # Simulator_stuff.LOCK.acquire(True,0.1)
        #time.sleep(Common.CHUNK_CADENCE)  # Simulates bit-rate control
        # C -> Chunk, L -> Loss, G -> Goodbye, B -> Broken, P -> Peer, M -> Monitor, R -> Ready
        #if __debug__:
            #sys.stderr.write(str(len(self.team))); sys.stderr.flush()
        time.sleep(psutil.cpu_percent()/4000.0)
        return b'C'

    def say_goodbye(self, peer):
        super().say_goodbye(peer)
        self.lg.info(f"{self.id}: sent [goodbye] to {peer}")

    def run__waiting_feedback(self):
        self.lg.info(f"{self.id}: waiting for a monitor peer")

    def run__index_error_feedback(self):
        self.lg.warning(f"{self.id}: the peer with index {self.peer_number} does not exist. peers_list={self.team} peer_number={self.peer_number}")

    def run__destinations_feedback(self):
        self.lg.debug(f"{self.id}: showing destination_of_chunk:\n")
        counter = 0
        for i in self.destination_of_chunk:
            self.lg.debug(f"{counter} -> {i} ")
            counter += 1

    def provide_feedback(self, peer_number, chunk_number):
        if Simulator_stuff.FEEDBACK:
            Simulator_stuff.FEEDBACK["STATUS"].put(("R", self.current_round))
            Simulator_stuff.FEEDBACK["DRAW"].put(("R", self.current_round))
            #Simulator_stuff.FEEDBACK["DRAW"].put(("T", "M", self.number_of_monitors, self.current_round))
            #Simulator_stuff.FEEDBACK["DRAW"].put(("T", "P", (len(self.team) - self.number_of_monitors), self.current_round))

        if peer_number == 0:
            self.current_round += 1
            sys.stderr.write(f" {colorama.Fore.YELLOW}{self.current_round}{colorama.Style.RESET_ALL}"); sys.stderr.flush()
            #self.lg.info("round = {}".format(self.current_round))
            #sys.stderr.write(f"{self.id}: round={self.current_round:03}/{self.number_of_rounds:03} chunk_number={chunk_number:05} number_of_peers={len(self.team):03}\r")
            #print("{}: len(peers_list)={}".format(self.id, len(self.team)))
            #sys.stderr.write(str(self.current_round) + "/" + str(self.max_number_of_rounds) + " " + str(self.chunk_number) + " " + str(len(self.team)) + "\r")

    def run__waiting_goodbyes_feedback(self):
        self.lg.info("{}: waiting for [goodbye]s from peers (peers_list={})".format(self.id, self.team))
            
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
