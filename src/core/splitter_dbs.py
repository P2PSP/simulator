"""
@package p2psp-simulator
splitter_dbs module
"""

# DBS (Data Broadcasting Set) layer

# DBS is the most basic layer to provide communication among splitter
# (source of the stream) and peers (destination of the stream), using
# unicast transmissions. The splitter sends a different chunk of
# stream to each peer, using a random round-robin scheduler (in each
# round peers are selected at random, but all peers are sent a chunk,
# in a round).

from .common import Common
from threading import Thread
import time
from .simulator_stuff import Simulator_stuff
from .simulator_stuff import Socket_print as socket
from .simulator_stuff import lg
import sys

class Splitter_DBS(Simulator_stuff):

    MAX_NUMBER_OF_LOST_CHUNKS = 32

    def __init__(self):
        self.id = "S"
        self.alive = True                                              # While True, keeps the splitter alive
        self.chunk_number = 0                                          # First chunk (number) to send
        self.peer_list = []                                            # Current peers in the team
        self.losses = {}                                               # (Detected) lost chunks per peer
        self.destination_of_chunk = []                                 # Destination peer of the buffered chunks
        self.buffer_size = Common.BUFFER_SIZE                          # Buffer (of chunks) size
        self.peer_number = 0                                           # First peer to serve in the list of peers
        self.max_number_of_chunk_loss = self.MAX_NUMBER_OF_LOST_CHUNKS # More lost, team removing
        self.number_of_monitors = 0                                    # Monitors report lost chunks
        self.outgoing_peer_list = []                                   # Peers which requested to leave the team
        self.current_round = 0                                         # Number of round (maybe not here).

        lg.info("{}: DBS initialized".format(self.id))

    def setup_peer_connection_socket(self):
        self.peer_connection_socket = socket(socket.AF_UNIX, socket.SOCK_STREAM) # Implementation dependent
        self.peer_connection_socket.set_id(self.id)
        self.peer_connection_socket.bind("S_tcp")
        self.peer_connection_socket.listen(1)

    def setup_team_socket(self):
        self.team_socket = socket(socket.AF_UNIX, socket.SOCK_DGRAM) # Implementation dependent
        self.team_socket.set_id(self.id)
        self.team_socket.bind("S_udp")
        
    def send_chunk(self, chunk, peer):
        #self.sendto(chunk, peer)
        try:
            self.team_socket.sendto("is", chunk, peer) # Implementation dependent by "is"
        except BlockingIOError: # Imp. dep.
            sys.stderr.write("sendto: full queue\n")

    def receive_chunk(self):
        # Simulator_stuff.LOCK.acquire(True,0.1)
        time.sleep(0.05)  # Simulates bit-rate control
        # C->Chunk, L->Los, G->Goodbye, B->Broken, P->Peer, M->Monitor, R-> Ready
        return "C"

    def handle_arrivals(self):
        while(self.alive):
            peer_serve_socket, peer = self.peer_connection_socket.accept()
            peer_serve_socket = socket(sock=peer_serve_socket)
            peer_serve_socket.set_id(peer)
            lg.info("{}: connection from {}".format(self.id, peer))
            Thread(target=self.handle_a_peer_arrival, args=((peer_serve_socket, peer),)).start()

    def handle_a_peer_arrival(self, connection):

        serve_socket = connection[0]
        incoming_peer = connection[1]

        lg.info("{}: acepted connection from peer".format(self.id, incoming_peer))

        self.send_buffer_size(serve_socket)
        self.send_the_number_of_peers(serve_socket)
        self.send_the_list_of_peers(serve_socket)

        lg.info("{}: waiting for incoming peer".format(self.id))
        message = serve_socket.recv("s")
        lg.info("{}: received {} from {}".format(self.id, message, incoming_peer))

        self.insert_peer(incoming_peer)

        # ------------------
        Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "IN", incoming_peer))
        # ------------------

        if (incoming_peer[0] == "M"):
            self.number_of_monitors += 1
        lg.info("{}: number of monitors = {}".format(self.id, self.number_of_monitors))

        serve_socket.close()

    def send_buffer_size(self, peer_serve_socket):
        lg.info("{}: sending buffer size = {}".format(self.id, self.buffer_size))
        peer_serve_socket.sendall("H", self.buffer_size)

    def send_the_number_of_peers(self, peer_serve_socket):
        lg.info("{}: sending number of monitors = {}".format(self.id, self.number_of_monitors))
        peer_serve_socket.sendall("H", self.number_of_monitors)
        lg.info("{}: sending list of peers of length = {}".format(self.id, self.peer_list))
        peer_serve_socket.sendall("H", len(self.peer_list))

    def send_the_list_of_peers(self, peer_serve_socket):
        lg.info("{}: sending peer list = {}".format(self.id, self.peer_list))
        for p in self.peer_list:
            peer_serve_socket.sendall("6s", p)

    def insert_peer(self, peer):
        if peer not in self.peer_list:
            self.peer_list.append(peer)
        self.losses[peer] = 0
        lg.info("{}: {} inserved in the team".format(self.id, peer))

    def increment_unsupportivity_of_peer(self, peer):
        try:
            self.losses[peer] += 1
        except KeyError:
            lg.error("{}: unexpected error, the unsupportive peer {} does not exist!".format(peer)) 
        else:
            lg.info("{}: peer {} has lost {} chunks".format(self.id, peer, self.losses[peer]))
            if self.losses[peer] > Common.MAX_CHUNK_LOSS:
                lg.info("{}: {} removed".format(self.id, peer))
                self.remove_peer(peer)
        finally:
           pass     

    def process_lost_chunk(self, lost_chunk_number, sender):
        destination = self.get_losser(lost_chunk_number)
        lg.info("{}: sender {} complains about lost chunk {} with destination {}".format(self.id, sender, lost_chunk_number, destination))
        self.increment_unsupportivity_of_peer(destination)

    def get_lost_chunk_number(self, message):
        return message[0]

    def get_losser(self, lost_chunk_number):
        return self.destination_of_chunk[lost_chunk_number % self.buffer_size]

    def remove_peer(self, peer):
        try:
            self.peer_list.remove(peer)
        except ValueError:
            lg.error("{}: unexpected error, the removed peer {} does not exist!".format(self.id, peer))
        else:
            #self.peer_number -= 1
            # --------------------
            Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "OUT", peer))
            if peer[0] == "M" and peer[1] != "P":
                self.number_of_monitors -= 1
            # --------------------
        #finally:
        #    pass

        try:
            del self.losses[peer]
        except KeyError:
            lg.error("{} unexpected error, the removed peer {} does not exist in losses".format(self.id, peer))
        finally:
            pass

    def process_goodbye(self, peer):
        lg.info("{}: received [goodbye] from".format(self.id, peer))
        if peer not in self.outgoing_peer_list:
            if peer in self.peer_list:
                self.outgoing_peer_list.append(peer)
                lg.info("{}: marked for deletion".format(self.id, peer))

    def say_goodbye(self, peer):
        goodbye = (-1, "G")
        self.team_socket.sendto("is", goodbye, peer)

    def remove_outgoing_peers(self):
        for p in self.outgoing_peer_list:
            self.say_goodbye(p)
            self.remove_peer(p)
        self.outgoing_peer_list.clear()

    def on_round_beginning(self):
        self.remove_outgoing_peers()

    def moderate_the_team(self):
        while self.alive:
            message, sender = self.team_socket.recvfrom("is")
            if (message[1] == "L"):
                lost_chunk_number = self.get_lost_chunk_number(message)
                self.process_lost_chunk(lost_chunk_number, sender)
            else:
                self.process_goodbye(sender)

    def reset_counters(self):
        for i in self.losses:
            self.losses[i] /= 2

    def reset_counters_thread(self):
        while self.alive:
            self.reset_counters()
            time.sleep(Common.COUNTERS_TIMING)

    def compute_next_peer_number(self, peer):
        self.peer_number = (self.peer_number + 1) % len(self.peer_list)

    def start(self):
        Thread(target=self.run).start()

    def run(self):
        self.setup_peer_connection_socket()
        self.setup_team_socket()

        Thread(target=self.handle_arrivals).start()
        Thread(target=self.moderate_the_team).start()
        Thread(target=self.reset_counters_thread).start()

        while self.alive:
            chunk = self.receive_chunk()
            if self.peer_number == 0:
                self.on_round_beginning() # Remove outgoing peers

                # -------------------
                lg.info("{}: current round {}".format(self.id, self.current_round))
                Simulator_stuff.FEEDBACK["STATUS"].put(("R", self.current_round))
                Simulator_stuff.FEEDBACK["DRAW"].put(("R", self.current_round))
                Simulator_stuff.FEEDBACK["DRAW"].put(("T", "M", self.number_of_monitors, self.current_round))
                Simulator_stuff.FEEDBACK["DRAW"].put(("T", "P", (len(self.peer_list)-self.number_of_monitors), self.current_round))
                # -------------------
            try:
                peer = self.peer_list[self.peer_number]
                message = (self.chunk_number, chunk)
                self.destination_of_chunk.insert(self.chunk_number % self.buffer_size, peer)
                self.send_chunk(message, peer)
                self.chunk_number = (self.chunk_number + 1) % Common.MAX_CHUNK_NUMBER
                self.compute_next_peer_number(peer)
            except IndexError:
                lg.error("{}: the monitor peer has died!".format(self.id))
                lg.error("{}: peer_list = {}".format(self.id, self.peer_list))
                lg.error("{}: peer_number = {}".format(self.id, self.peer_number))

            if self.peer_number == 0:
                self.current_round += 1
