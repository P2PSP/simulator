"""
@package p2psp-simulator
splitter_dbs module
"""

from .common import Common
from threading import Thread
import time
from .simulator_stuff import Simulator_stuff
from .simulator_stuff import Socket_print as socket
import sys


class Splitter_DBS(Simulator_stuff):

    MAX_NUMBER_OF_LOST_CHUNKS = 32

    def __init__(self):
        self.id = "S"
        self.alive = True  # While True, keeps the splitter alive
        self.chunk_number = 0  # First chunk number to broadcast
        self.peer_list = []  # Current peers in the team
        self.losses = {}  # Lost chunks per peer
        self.destination_of_chunk = []  # Destination peer of the buffered chunks
        self.buffer_size = Common.BUFFER_SIZE  # Buffer (of chunks) size
        self.peer_number = 0  # First peer to serve in the list of peers
        self.max_number_of_chunk_loss = self.MAX_NUMBER_OF_LOST_CHUNKS
        self.number_of_monitors = 0
        self.outgoing_peer_list = []  # Peers which requested to leave the team
        self.current_round = 0

        print(self.id, ": DBS initialized")

    def setup_peer_connection_socket(self):
        self.peer_connection_socket = socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.peer_connection_socket.set_id(self.id)
        self.peer_connection_socket.bind("S_tcp")
        self.peer_connection_socket.listen(1)

    def setup_team_socket(self):
        self.team_socket = socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.team_socket.set_id(self.id)
        self.team_socket.bind("S_udp")
        
    def send_chunk(self, chunk, peer):
        #self.sendto(chunk, peer)
        try:
            self.team_socket.sendto("is", chunk, peer)
        except BlockingIOError:
            sys.stderr.write("sendto: full queue\n")
        else:
            self.chunk_number = (self.chunk_number + 1) % Common.MAX_CHUNK_NUMBER



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
            print("Connection from ", peer)
            Thread(target=self.handle_a_peer_arrival, args=((peer_serve_socket, peer),)).start()

    def handle_a_peer_arrival(self, connection):

        serve_socket = connection[0]
        incoming_peer = connection[1]

        print(self.id, ": acepted connection from peer", incoming_peer)

        self.send_buffer_size(serve_socket)
        self.send_the_number_of_peers(serve_socket)
        self.send_the_list_of_peers(serve_socket)

        print(self.id, ": waiting for outgoing peer")
        message = serve_socket.recv("s")
        print(self.id, ": received", message, "from", incoming_peer)

        self.insert_peer(incoming_peer)

        # ------------------
        Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "IN", incoming_peer))
        # ------------------

        if (incoming_peer[0] == "M"):
            self.number_of_monitors += 1
        print(self.id, ": number of monitors", self.number_of_monitors)

        serve_socket.close()

    def send_buffer_size(self, peer_serve_socket):
        print(self.id, ": sending buffer size =", self.buffer_size)
        peer_serve_socket.sendall("H", self.buffer_size)

    def send_the_number_of_peers(self, peer_serve_socket):
        print(self.id, ": sending number of monitors =", self.number_of_monitors)
        peer_serve_socket.sendall("H", self.number_of_monitors)
        print(self.id, ": sending list of peers of length =", len(self.peer_list))
        peer_serve_socket.sendall("H", len(self.peer_list))

    def send_the_list_of_peers(self, peer_serve_socket):
        print(self.id, ": sending peer list =", self.peer_list)
        for p in self.peer_list:
            peer_serve_socket.sendall("6s", p)

    def insert_peer(self, peer):
        if peer not in self.peer_list:
            self.peer_list.append(peer)
        self.losses[peer] = 0
        print(self.id, ":", peer, "inserted in the team")

    def increment_unsupportivity_of_peer(self, peer):
        try:
            self.losses[peer] += 1
        except KeyError:
            print(self.id, ": unexpeted error, the unsupportive peer", peer, "does not exist!")
        else:
            print(self.id, ":", peer, "has loss", self.losses[peer], "chunks")
            if self.losses[peer] > Common.MAX_CHUNK_LOSS:
                print(peer, 'removed')
                self.remove_peer(peer)
        finally:
           pass     

    def process_lost_chunk(self, lost_chunk_number, sender):
        destination = self.get_losser(lost_chunk_number)
        print(self.id, ":", sender, "complains about lost chunk", lost_chunk_number, "destination", destination)
        self.increment_unsupportivity_of_peer(destination)

    def get_lost_chunk_number(self, message):
        return message[0]

    def get_losser(self, lost_chunk_number):
        return self.destination_of_chunk[lost_chunk_number % self.buffer_size]

    def remove_peer(self, peer):
        try:
            self.peer_list.remove(peer)
        except ValueError:
            print(self.id, ": unexpected error, the removed peer", peer, "does not exist!")
        else:
            #self.peer_number -= 1
            # --------------------
            Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "OUT", peer))
            if peer[0] == "M" and peer[1] != "P":
                self.number_of_monitors -= 1
            # --------------------
        finally:
            pass

        try:
            del self.losses[peer]
        except KeyError:
            print(self.id, ": unexpected error, the removed peer", peer, "does not exist in losses")
        finally:
            pass

    def process_goodbye(self, peer):
        print(self.id, ": received goodbye from", peer)
        if peer not in self.outgoing_peer_list:
            if peer in self.peer_list:
                self.outgoing_peer_list.append(peer)
                print(self.id, ": marked for deletion", peer)

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
                print("Splitter: round", self.current_round)
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
                self.compute_next_peer_number(peer)
            except IndexError:
                print(self.id, ": the monitor peer has died!")
                print(self.id, ": peer_list =", self.peer_list)
                print(self.id, ": peer_number =", self.peer_number)

            if self.peer_number == 0:
                self.current_round += 1
