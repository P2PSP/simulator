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

class Splitter_DBS():

    def __init__(self,
                 buffer_size = 32,
                 max_chunk_loss = 16,
                 number_of_rounds = 100,
                 name="Splitter_DBS",
                 loglevel = logging.ERROR
    ):
        self.lg = logging.getLogger(name)
        self.lg.setLevel(loglevel)
        self.name = name
        self.buffer_size = buffer_size
        self.max_chunk_loss = max_chunk_loss
    
        self.alive = True  # While True, keeps the splitter alive
        self.chunk_number = 0  # First chunk (number) to send
        self.team = []  # Current peers in the team
        self.losses = {}  # (Detected) lost chunks per peer
        self.destination_of_chunk = (buffer_size*2)*[0]
        #self.destination_of_chunk = {}
        self.peer_number = 0  # First peer to serve in the list of peers
        self.number_of_monitors = 0  # Monitors report lost chunks
        self.outgoing_peers_list = []  # Peers which requested to leave the team

        self.chunk_packet_format = "!isIi"

        self.current_round = 0  # Number of round (maybe not here).
#        self.chunk_cadence = chunk_cadence
        self.peer_index_in_team = 0
        #self.received_chunks_from = {}
        #self.lost_chunks_from = {}

        self.lg.debug(f"{name}: initialized")

    def setup_peer_connection_socket(self, port=0):
        self.peer_connection_socket = socket(family=socket.AF_INET, type=socket.SOCK_STREAM, loglevel=self.lg.level)
        self.peer_connection_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.peer_connection_socket.set_id(self.id)
        #host = socket.gethostbyname(socket.gethostname())
        self.peer_connection_socket.bind(('', port))
        self.id = self.peer_connection_socket.getsockname()
        self.lg.info(f"{self.id}: I am the splitter")
        self.peer_connection_socket.listen(1)

    def setup_team_socket(self):
        self.team_socket = socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.team_socket.set_id(self.id)
        self.team_socket.bind(self.id)
        # self.team_socket.set_max_packet_size(struct.calcsize("is3s")) # Chunck index, chunk, origin

    def send_chunk(self, chunk_number, chunk, peer):
        # self.lg.info("splitter_dbs.send_chunk({}, {})".format(chunk_msg, peer))
        #msg = struct.pack("isli", *chunk_msg)
        # msg = struct.pack("is3s", chunk_msg[0], bytes(chunk_msg[1]), chunk_msg[2])
        chunk_msg = self.compose_chunk_packet(chunk_number = chunk_number,
                                              chunk = chunk,
                                              peer = peer)
        self.team_socket.sendto(chunk_msg, peer)
        self.lg.info(f"{self.id}: chunk {chunk_number} sent to {peer}")

    def handle_arrivals(self):
        while self.alive:
            peer_serve_socket, peer = self.peer_connection_socket.accept()
            peer_serve_socket = socket(sock=peer_serve_socket)
            # peer_serve_socket.set_id(peer)
            self.lg.info(f"{self.id}: new connection from incoming {peer}")
            Thread(target=self.handle_a_peer_arrival, args=((peer_serve_socket, peer),)).start()

    #def send_the_header(self):
    #    pass

    # Depends on the application
    def send_the_chunk_size(self, peer_serve_socket):
        pass

    # Depends on the application
    def send_header_bytes(self, peer_serve_socket):
        pass

    # Depends on the application
    def send_header(self, peer_serve_socket):
        pass

    # Depends on the application
    def handle_a_peer_arrival(self, connection):

        serve_socket = connection[0]
        incoming_peer = connection[1]

        self.lg.info(f"{self.id}: accepted connection from peer {incoming_peer}")
        
        self.send_peer_index_in_team(serve_socket, len(self.team))
        self.send_the_chunk_size(serve_socket)
        self.send_public_endpoint(incoming_peer, serve_socket)
        self.send_buffer_size(serve_socket)
        self.send_header_bytes(serve_socket)
        self.send_header(serve_socket)
        self.send_the_number_of_peers(serve_socket)
        self.send_the_list_of_peers(serve_socket)

        # ??????????????????????????????
        #msg_length = struct.calcsize("s")
        #msg = serve_socket.recv(msg_length)
        #message = struct.unpack("s", msg)[0]

        self.insert_peer(incoming_peer)
        serve_socket.close()

    def send_public_endpoint(self, endpoint, peer_serve_socket):
        self.lg.info(f"{self.id}: sending peer's (public) endpoint={endpoint}")
        # peer_serve_socket.sendall(Splitter_DBS.buffer_size, "H")
        msg = struct.pack("!Ii", IP_tools.ip2int(endpoint[0]), endpoint[1])
        peer_serve_socket.sendall(msg)

    def send_buffer_size(self, peer_serve_socket):
        # peer_serve_socket.sendall(Splitter_DBS.buffer_size, "H")
        msg = struct.pack("!H", self.buffer_size)
        peer_serve_socket.sendall(msg)

    def send_the_number_of_peers(self, peer_serve_socket):
#        self.lg.info(f"{self.id}: sending number_of_monitors={self.number_of_monitors}")
        # peer_serve_socket.sendall(self.number_of_monitors, "H")
        #msg = struct.pack("!H", self.number_of_monitors)
        #peer_serve_socket.sendall(msg)
        self.lg.info(f"{self.id}: sending peers_list of length={len(self.team)}")
        # peer_serve_socket.sendall(len(self.team), "H")
        msg = struct.pack("!H", len(self.team))
        peer_serve_socket.sendall(msg)

    def send_peer_index_in_team(self, peer_serve_socket, peer_index_in_team):
        self.lg.info(f"{self.id}: sending peer_index_in_team={peer_index_in_team}")
        msg = struct.pack("!H", peer_index_in_team)
        peer_serve_socket.sendall(msg)

    def send_the_list_of_peers(self, peer_serve_socket):
        self.lg.info(f"{self.id}: sending peers_list={self.team}")
        counter = 0
        for p in random.sample(self.team, len(self.team)): # Peers are selected at random
            # peer_serve_socket.sendall(p, "6s")
            msg = struct.pack("!Ii", IP_tools.ip2int(p[0]), p[1])
            peer_serve_socket.sendall(msg)
            counter += 1
            #if counter > self.max_degree:
            #    break

    def insert_peer(self, peer):
        if peer not in self.team:
            self.team.append(peer)
        self.losses[peer] = 0
        self.lg.info(f"{self.id}: {peer} inserted in the team")

    def increment_unsupportivity_of_peer(self, peer):
        try:
            self.losses[peer] += 1
        except KeyError:
            self.lg.warning(f"{self.id}: the unsupportive peer {peer} does not exist in {self.losses}")
        else:
            self.lg.info(f"{self.id}: peer {peer} has lost {self.losses[peer]} chunks")
            if self.losses[peer] > self.max_chunk_loss:
                self.remove_peer(peer)
#        finally:
#            pass

    def reset_counters(self):
        for peer in self.losses.keys():
            self.losses[peer] /= 2
#            self.losses[peer] /= self.max_chunk_loss
#            if self.losses[peer] < 0:
#                self.losses[peer] = 0

    def process_lost_chunk(self, lost_chunk_number, sender):
        destination = self.get_losser(lost_chunk_number)
        self.lg.info(f"{self.id}: {sender} complains about lost chunk {lost_chunk_number} with destination {destination}")
        #self.total_lost_chunks += 1
        self.increment_unsupportivity_of_peer(destination)

    # def get_lost_chunk_number(self, message):
    #    return message[1]

    def get_losser(self, lost_chunk_number):
        #return self.destination_of_chunk[lost_chunk_number % self.buffer_size]
        return self.destination_of_chunk[lost_chunk_number % (self.buffer_size*2)]

    def del_peer(self, peer_index):
        del self.team[peer_index]
        
    def remove_peer(self, peer):
        try:
            peer_index = self.team.index(peer)
        except ValueError:
            self.lg.warning(f"{self.id}: the removed peer {peer} does not exist in {self.peer_list}")
        else:
            self.del_peer(peer_index)

        try:
            del self.losses[peer]
        except KeyError:
            self.lg.warning(f"{self.id}: the removed peer {peer} does not exist in losses!")
        finally:
            pass

    def process_goodbye(self, peer):
        self.lg.info(f"{self.id}: received [goodbye] from {peer}")
#        sys.stderr.write(f"{self.id}: received [goodbye] from {peer}\n")
        if peer not in self.outgoing_peers_list:
            if peer in self.team:
                self.outgoing_peers_list.append(peer)
                self.lg.info(f"{self.id}: {peer} marked for deletion")

    def say_goodbye(self, peer):
        # self.team_socket.sendto(Messages.GOODBYE, "i" , peer)
        msg = struct.pack("!i", Messages.GOODBYE)
        self.team_socket.sendto(msg, peer)
        self.lg.info(f"{self.id}: sent [goodbye] to {peer}")

    def remove_outgoing_peers(self):
        if __debug__:
            if len(self.outgoing_peers_list) > 0:
                sys.stderr.write(f"{self.id}: remove_outgoint_peers: len(outgoing_peers_list)={len(self.outgoing_peers_list)}\n")
        for p in self.outgoing_peers_list:
            self.say_goodbye(p)
            self.remove_peer(p)
            self.lg.info(f"{self.id}: outgoing peer {p}")
        self.outgoing_peers_list.clear()

    def on_round_beginning(self):
        self.remove_outgoing_peers()
        self.reset_counters()

    def moderate_the_team(self):
        while self.alive:
            # message, sender = self.team_socket.recvfrom()
            packed_msg, sender = self.team_socket.recvfrom(100)
            #print("{}: packet={}".format(self.id, packed_msg))

            # All parameters are unsigned int
            msg_format = '!' + 'i' * (len(packed_msg)//4)
#            self.lg.error(msg_format)
#            self.lg.error(packed_msg)
#            self.lg.error(len(packed_msg))
#            self.lg.error(sender)
            try:
                msg = struct.unpack(msg_format, packed_msg)
            except struct.error:
                self.lg.warning(f"{self.id}: unexpected message {packed_msg} with length={len(packed_msg)} received from {sender}")

            if msg[0] == Messages.GOODBYE:
                # Message sent by all peers when they leave the team
                self.process_goodbye(sender)

            elif msg[0] == Messages.LOST_CHUNK:
                # Message sent only by monitors when they lost a chunk
                lost_chunk_number = msg[1]
                # lost_chunk_number = self.get_lost_chunk_number(message)
                self.process_lost_chunk(lost_chunk_number, sender)
                self.lg.info(f"{self.id}: received [lost chunk {msg[1]}] from {sender}")
            elif msg[0] == Messages.HELLO:
                # Message sent by peers to create a translation entry in their NATS 
                self.lg.info(f"{self.id}: received [hello] from {sender}")
            else:
                self.lg.warning(f"{self.id}: unexpected message {packed_msg} with length={len(packed_msg)} decoded as {msg} received from {sender}")

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
        chunk_msg = (self.chunk_number,
                     chunk,
                     IP_tools.ip2int(peer[0]), # now,
                     peer[1])
        msg = struct.pack(self.chunk_packet_format, *chunk_msg)
        return msg

    def run(self):
        chunk_number = 0
        total_peers = 0

        Thread(target=self.handle_arrivals).start()
        Thread(target=self.moderate_the_team).start()
        #Thread(target=self.reset_counters_thread).start()

        while len(self.team) == 0:
            #print("{}: waiting for a monitor at {}"
            #      .format(self.id, self.id))
            self.lg.info(f"{self.id}: waiting for a monitor peer")
            time.sleep(1)
        print()

        while (len(self.team) > 0) and self.alive:
            chunk = self.retrieve_chunk()
            #sys.stderr.write(".\n")

            # ????
            #self.lg.info("peer_number = {}".format(self.peer_number))
            #print("peer_number = {}".format(self.peer_number))
            if self.peer_number == 0:
                total_peers += len(self.team)
                self.on_round_beginning()  # Remove outgoing peers

            try:
                peer = self.team[self.peer_number]

            except IndexError:
                self.lg.warning(f"{self.id}: the peer with index {self.peer_number} does not exist. peers_list={self.team} peer_number={self.peer_number}")
                # raise

            #message = self.compose_chunk_packet(chunk, peer)
            self.destination_of_chunk[self.chunk_number % (self.buffer_size*2)] = peer
            if __debug__:
                self.lg.debug(f"{self.id}: showing destination_of_chunk:\n")
                counter = 0
                for i in self.destination_of_chunk:
                    self.lg.debug(f"{counter} -> {i} ")
                    counter += 1
            #sys.stderr.write(str(message))
            self.send_chunk(chunk_number, chunk, peer)
            chunk_number = (chunk_number + 1) % Limits.MAX_CHUNK_NUMBER
            try:
                self.peer_number = (self.peer_number + 1) % len(self.team)
            except ZeroDivisionError:
                pass
            
            self.provide_feedback(self.peer_number, chunk_number)
            self.is_alive()

        self.lg.info(f"{self.id}: run: len(self.team)={len(self.team)}")
        #sys.stderr.write(f"{self.id}: run: len(self.team)={len(self.team)} \n")
        #self.alive = False
        self.lg.info(f"{self.id}: run: alive={self.alive}")
        #sys.stderr.write(f"{self.id}: run: alive={self.alive} \n")
        # Say "goodbye" to the peers and wait for their "goodbye"s
        counter = 0
        while (len(self.team) > 0) and (counter < 10):
        #while len(self.team) > 0:
            self.lg.info("{}: waiting for [goodbye]s from peers (peers_list={})".format(self.id, self.team))
            time.sleep(0.1)
            for p in self.team:
                self.say_goodbye(p)
            counter += 1

        #print("{}: total peers {} in {} rounds, {} peers/round".format(self.id, total_peers, self.current_round, (float)(total_peers)/(float)(self.current_round)))
        #print("{}: {} lost chunks of {}".format(self.id, self.total_lost_chunks, self.total_received_chunks, (float)(self.total_lost_chunks)/(float)(self.total_received_chunks)))
        #sys.stderr.write(f"{self.id}: goodbye!\n")
