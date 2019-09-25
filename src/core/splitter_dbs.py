"""
@package p2psp-simulator
splitter_dbs module
"""

# Abstract class.

# DBS (Data Broadcasting Set) layer, splitter side.

# DBS is the most basic layer to provide communication among splitter
# (source of the stream) and peers (destination of the stream), using
# unicast transmissions. The splitter sends a different chunk of
# stream to each peer, using a random round-robin scheduler.

import sys
import logging
# from .simulator_stuff import lg
import struct
# from threading import Lock
import time
from threading import Thread

from .messages import Messages
from .limits import Limits
from .socket_wrapper import Socket_wrapper as socket
from .ip_tools import IP_tools

# class Splitter_DBS(Simulator_stuff):
import random

import queue

class Splitter_DBS():

    def __init__(self,
                 buffer_size = 32,
                 max_chunk_loss = 16,
                 number_of_rounds = 100,
                 name="Splitter_DBS",
                 loglevel = logging.ERROR
    ):
        self.name = name
        self.buffer_size = buffer_size
        self.max_chunk_loss = max_chunk_loss
    
        self.alive = True  # While True, keeps the splitter alive
#        self.chunk_number = 0  # First chunk (number) to send
        self.team = []  # Current peers in the team
        self.losses = {}  # Reported (by monitors) lost chunks per peer
#        self.rounds_lossing = {}  # Number or consecutive rounds lossing the chunk sent from the splitter
        self.destination_of_chunk = (buffer_size)*[0]
        #self.destination_of_chunk = {}
        self.peer_number = 0  # First peer to serve in the list of peers
        self.number_of_monitors = 1  # Monitors report lost chunks
        self.outgoing_peers_list = []  # Peers which requested to leave the team

        self.chunk_packet_format = "!isIi"

        self.current_round = 0  # Number of round (maybe not here).
#        self.chunk_cadence = chunk_cadence
        self.peer_index_in_team = 0
        #self.received_chunks_from = {}
        #self.lost_chunks_from = {}
        self.total_losses = 0  # Total number of lost chunks (reset when a peer is removed)
        self.new_peers = queue.Queue()

    def setup_peer_connection_socket(self, port=0):
        self.peer_connection_socket = socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.peer_connection_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.peer_connection_socket.set_id(self.id)
        host = socket.gethostbyname(socket.gethostname())
        self.peer_connection_socket.bind(('', port))
        self.peer_connection_socket.listen(1)
        port = self.peer_connection_socket.getsockname()[1]
        self.id = (host, port)
        #sys.stderr.write(f" host={host}"); sys.stderr.flush()

    def setup_team_socket(self):
        self.team_socket = socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.team_socket.bind(self.id)

    def send_chunk(self, chunk_number, chunk, peer):
        chunk_msg = self.compose_chunk_packet(chunk_number = chunk_number,
                                              chunk = chunk,
                                              peer = peer)
        self.team_socket.sendto(chunk_msg, peer)

    def handle_arrivals__feedback(self):
        pass

    def handle_arrivals(self):
        while self.alive:
            peer_serve_socket, peer = self.peer_connection_socket.accept()
            peer_serve_socket = socket(sock=peer_serve_socket)
            self.handle_arrivals__feedback(peer)
            #Thread(target=self.handle_a_peer_arrival, args=((peer_serve_socket, peer),)).start() # UNSAFE!!!
            self.handle_a_peer_arrival((peer_serve_socket, peer))

    # Depends on the application
    def send_the_chunk_size(self, peer_serve_socket):
        pass

    # Depends on the application
    def send_the_header_bytes(self, peer_serve_socket):
        pass

    # Depends on the application
    def send_the_header(self, peer_serve_socket):
        pass

    # Depends on the application
    def handle_a_peer_arrival(self, connection):
        serve_socket = connection[0]
        incoming_peer = connection[1]
        #sys.stderr.write(f" ->{incoming_peer}"); sys.stderr.flush()
        self.send_the_public_endpoint(incoming_peer, serve_socket)
        self.send_the_peer_index_in_team(serve_socket, len(self.team))
        self.send_the_number_of_peers(serve_socket)
        self.send_the_list_of_peers(serve_socket)
        self.send_the_buffer_size(serve_socket)
        self.send_the_chunk_size(serve_socket)
        self.send_the_header_bytes(serve_socket)
        self.send_the_header(serve_socket)

        # ??????????????????????????????
        #msg_length = struct.calcsize("s")
        #msg = serve_socket.recv(msg_length)
        #message = struct.unpack("s", msg)[0]

        self.insert_peer(incoming_peer)
        #self.new_peers.put(incoming_peer)
        serve_socket.close()

    def send_the_public_endpoint(self, endpoint, peer_serve_socket):
        msg = struct.pack("!Ii", IP_tools.ip2int(endpoint[0]), endpoint[1])
        peer_serve_socket.sendall(msg)

    def send_the_buffer_size(self, peer_serve_socket):
        msg = struct.pack("!H", self.buffer_size)
        peer_serve_socket.sendall(msg)

    def send_the_number_of_peers(self, peer_serve_socket):
        msg = struct.pack("!H", len(self.team))
        peer_serve_socket.sendall(msg)

    def send_the_peer_index_in_team(self, peer_serve_socket, peer_index_in_team):
        msg = struct.pack("!H", peer_index_in_team)
        peer_serve_socket.sendall(msg)

    def send_the_list_of_peers(self, peer_serve_socket):
        counter = 0
        for p in random.sample(self.team, len(self.team)): # Peers are selected at random
        #for p in self.team:
            # peer_serve_socket.sendall(p, "6s")
            msg = struct.pack("!Ii", IP_tools.ip2int(p[0]), p[1])
            peer_serve_socket.sendall(msg)
            counter += 1
        #sys.stderr.write(f" ->{len(self.team)}"); sys.stderr.flush()

    def insert_peer(self, peer):
        #sys.stderr.write(f" ->{peer}")
        if peer not in self.team:
            self.team.append(peer)
        self.losses[peer] = 0

    def increment_unsupportivity_of_peer__warning(self, peer):
        pass
        
    def increment_unsupportivity_of_peer(self, peer):
        try:
            self.losses[peer] += 1
        except KeyError:
            self.increment_unsupportivity_of_peer__warning(peer)
        else:
            if self.total_losses > self.max_chunk_loss:
                peer_to_remove = max(self.losses, key=self.losses.get)
                self.remove_peer(peer_to_remove)
                # Reset the counters
                for peer in self.losses.keys():
                    self.losses[peer] = 0
                self.total_losses = 0

    def process_lost_chunk(self, lost_chunk_number):
        self.total_losses += 1
        destination = self.get_losser(lost_chunk_number)
        if destination in self.team:
            if self.team.index(destination) >= self.number_of_monitors:
                self.increment_unsupportivity_of_peer(destination)

    def get_losser(self, lost_chunk_number):
        return self.destination_of_chunk[lost_chunk_number % (self.buffer_size)]

    def del_peer(self, peer_index):
        del self.team[peer_index]

    def remove_peer__warning1(self, peer):
        pass

    def remove_peer__warning2(self, peer):
        pass
    
    def remove_peer(self, peer):
        try:
            peer_index = self.team.index(peer)
        except ValueError:
            self.remove_peer__warning1(peer)
        else:
            self.del_peer(peer_index)

        try:
            del self.losses[peer]
        except KeyError:
            self.remove_peer__warning2(peer)
        finally:
            pass

    def process_goodbye__feedback(self, peer):
        pass
        
    def process_goodbye(self, peer):
        if peer not in self.outgoing_peers_list:
            if peer in self.team:
                self.outgoing_peers_list.append(peer)
                self.process_goodbye__feedback(peer)

    def say_goodbye(self, peer):
        msg = struct.pack("!i", Messages.GOODBYE)
        self.team_socket.sendto(msg, peer)

    def remove_outgoing_peers__feedback(self, peer):
        pass
        
    def remove_outgoing_peers(self):
        for p in self.outgoing_peers_list:
            self.say_goodbye(p)
            self.remove_peer(p)
            self.remove_outgoing_peers__feedback(p)
        self.outgoing_peers_list.clear()

    def on_round_beginning(self):
        self.remove_outgoing_peers()
        #while not self.new_peers.empty():
        #    self.insert_peer(self.new_peers.get())
        #self.reset_counters()

    def moderate_the_team__warning1(self, packed_msg, sender):
        pass

    def moderate_the_team__warning2(self, msg, sender):
        pass

    def moderate_the_team__warning3(self, packed_msg, msg, sender):
        pass

    def moderate_the_team__hello_feedback(self, sender):
        pass

    def moderate_the_team(self):
        while self.alive:
            # message, sender = self.team_socket.recvfrom()
            packed_msg, sender = self.team_socket.recvfrom(100)
            #print("{}: packet={}".format(self.id, packed_msg))

            # All parameters are unsigned int
            msg_format = '!' + 'i' * (len(packed_msg)//4)
            try:
                msg = struct.unpack(msg_format, packed_msg)
            except struct.error:
                self.moderate_the_team__warning1(packed_msg, sender)

            if msg[0] == Messages.GOODBYE:
                # Message sent by all peers when they leave the team
                self.process_goodbye(sender)

            elif msg[0] == Messages.LOST_CHUNK:
                # Message sent only by monitors when they lost a chunk
                lost_chunk_number = msg[1]
                self.process_lost_chunk(lost_chunk_number)
                self.moderate_the_team__warning2(msg, sender)
                
            elif msg[0] == Messages.HELLO:
                # Message sent by peers to create a translation entry
                # in their NATs. No extra functionality by now.
                self.moderate_the_team__hello_feedback(sender)
            else:
                self.moderate_the_team__warning3(packed_msg, msg, sender)

    #def reset_counters_thread(self):
    #    while self.alive:
    #        self.reset_counters()
    #        time.sleep(Common.COUNTERS_TIMING)

    def compute_next_peer_number(self, peer):
        try:
            self.peer_number = (self.peer_number + 1) % len(self.team)
        except ZeroDivisionError:
            pass

    def start(self):
        Thread(target=self.run).start()

    def get_id(self):
        return self.id

    def compose_chunk_packet(self, chunk_number, chunk, peer):
        #now = time.time()
        chunk_msg = (chunk_number,
                     chunk,
                     IP_tools.ip2int(peer[0]), # now,
                     peer[1])
        msg = struct.pack(self.chunk_packet_format, *chunk_msg)
        return msg

    def run__waiting_feedback(self):
        pass

    def run__index_error_feedback(self):
        pass

    def run__destinations_feedback(self):
        pass

    def run__waiting_goodbyes_feedback(self):
        pass
    
    def run(self):
        chunk_number = 0
        total_peers = 0

        Thread(target=self.handle_arrivals).start()
        Thread(target=self.moderate_the_team).start()
        #Thread(target=self.reset_counters_thread).start()

        while len(self.team) == 0:
            time.sleep(1)
            #self.on_round_beginning()
        print()

        while (len(self.team) > 0) and self.alive:
            chunk = self.retrieve_chunk()
            if self.peer_number == 0:
                total_peers += len(self.team)
                self.on_round_beginning()

            try:
                peer = self.team[self.peer_number]
            except IndexError:
                self.run__index_error_feedback()

            self.destination_of_chunk[chunk_number % (self.buffer_size)] = peer  # self.team.index(peer)
            self.run__destinations_feedback()
            self.send_chunk(chunk_number, chunk, peer)
            chunk_number = (chunk_number + 1) % Limits.MAX_CHUNK_NUMBER
            try:
                self.peer_number = (self.peer_number + 1) % len(self.team)
            except ZeroDivisionError:
                pass
            
            self.provide_feedback(self.peer_number, chunk_number)
            self.is_alive()

        # Say "goodbye" to the peers and wait for their "goodbye"s
        counter = 0
        while (len(self.team) > 0) and (counter < 10):
        #while len(self.team) > 0:
            self.run__waiting_goodbyes_feedback()
            time.sleep(0.1)
            for p in self.team:
                self.say_goodbye(p)
            counter += 1

        #print("{}: total peers {} in {} rounds, {} peers/round".format(self.id, total_peers, self.current_round, (float)(total_peers)/(float)(self.current_round)))
        #print("{}: {} lost chunks of {}".format(self.id, self.total_lost_chunks, self.total_received_chunks, (float)(self.total_lost_chunks)/(float)(self.total_received_chunks)))
        #sys.stderr.write(f"{self.id}: goodbye!\n")
