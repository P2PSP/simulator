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
import colorama

from .messages import Messages
from .limits import Limits
from .socket_wrapper import Socket_wrapper as socket
from .ip_tools import IP_tools

# class Splitter_DBS(Simulator_stuff):
import random
import core.stderr as stderr

class Splitter_DBS():

    def __init__(self,
                 buffer_size = 32,
                 max_chunk_loss = 16,
                 name="Splitter_DBS"):
        self.name = name
        self.buffer_size = buffer_size
        self.max_chunk_loss = max_chunk_loss
        self.alive = True                                                       # While True, keeps the splitter alive
        self.team = []                                                          # Current peers in the team
        self.losses = {}                                                        # Reported (by monitors) lost chunks per peer
        self.destination_of_chunk = (buffer_size)*[0]
        self.peer_number = 0                                                    # First peer to serve in the list of peers
        self.number_of_monitors = 1
        self.outgoing_peers_list = []                                           # Peers which requested to leave the team
        self.packet_format()
        self.peer_index_in_team = 0
        self.total_losses = 0                                                   # Total number of lost chunks (reset when a peer is removed)

        logging.basicConfig(stream=sys.stdout, format="%(asctime)s.%(msecs)03d %(message)s %(levelname)-8s %(name)s %(pathname)s:%(lineno)d", datefmt="%H:%M:%S")
        self.lg = logging.getLogger(__name__)
        if __debug__:
            self.lg.setLevel(logging.DEBUG)
        else:
            self.lg.setLevel(logging.ERROR)

    def packet_format(self):
        self.chunk_packet_format = "!isIi"
            
    def setup_peer_connection_socket(self, port=0):
        self.peer_connection_socket = socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.peer_connection_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.peer_connection_socket.set_id(self.id)
        #host = socket.gethostbyname(socket.gethostname())
        host_name = socket.gethostname()
        for i in range(3):
            while True:
                try:
                    address = socket.gethostbyname(host_name)
                except socket.gaierror:
                    continue
                break
        self.peer_connection_socket.bind(('', port))
        self.peer_connection_socket.listen(1)
        port = self.peer_connection_socket.getsockname()[1]
        self.id = (address, port)
        #stderr.write(f" host={host}")
        self.lg.debug(f"{self.id}: I am the splitter")

    def setup_team_socket(self):
        self.team_socket = socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.team_socket.bind(self.id)

    def send_chunk(self, chunk_number, chunk, peer):
        chunk_msg = self.compose_chunk_packet(chunk_number = chunk_number,
                                              chunk = chunk,
                                              peer = peer)
        self.team_socket.sendto(chunk_msg, peer)
        self.lg.debug(f"{self.id}: chunk {chunk_number} sent to {peer}")

    def handle_arrivals(self):
        while self.alive:
            peer_serve_socket, peer = self.peer_connection_socket.accept()
            peer_serve_socket = socket(sock=peer_serve_socket)
            self.lg.info(f"{self.id}: new connection from incoming {peer}")
            #Thread(target=self.handle_a_peer_arrival, args=((peer_serve_socket, peer),)).start() # UNSAFE!!!
            self.handle_a_peer_arrival((peer_serve_socket, peer))

    # Depends on the application
    def handle_a_peer_arrival(self, connection):
        serve_socket = connection[0]
        incoming_peer = connection[1]
        #stderr.write(f" ->{incoming_peer}")
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
        self.lg.debug(f"{self.id}: accepted peer {incoming_peer}")        

    def send_the_public_endpoint(self, endpoint, peer_serve_socket):
        self.lg.debug(f"{self.id}: sending peer's (public) endpoint={endpoint}")
        msg = struct.pack("!Ii", IP_tools.ip2int(endpoint[0]), endpoint[1])
        peer_serve_socket.sendall(msg)

    def send_the_buffer_size(self, peer_serve_socket):
        self.lg.debug(f"{self.id}: sending buffer_size={self.buffer_size}")
        msg = struct.pack("!H", self.buffer_size)
        peer_serve_socket.sendall(msg)

    def send_the_number_of_peers(self, peer_serve_socket):
        self.lg.debug(f"{self.id}: sending peers_list of length={len(self.team)}")
        msg = struct.pack("!H", len(self.team))
        peer_serve_socket.sendall(msg)

    def send_the_peer_index_in_team(self, peer_serve_socket, peer_index_in_team):
        self.lg.debug(f"{self.id}: sending peer_index_in_team={peer_index_in_team}")
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
        #stderr.write(f" ->{len(self.team)}")
        self.lg.debug(f"{self.id}: list of peers sent ({len(self.team)} peers)")

    def insert_peer(self, peer):
        if peer not in self.team:
            self.team.append(peer)
        self.losses[peer] = 0
        self.lg.debug(f"{self.id}: {peer} inserted in the team")
        stderr.write(f" {colorama.Fore.MAGENTA}{len(self.team)}{colorama.Style.RESET_ALL}")

    def increment_unsupportivity_of_peer(self, peer):
        stderr.write(f" {colorama.Fore.RED}({self.team.index(peer)}){colorama.Style.RESET_ALL}")
        try:
            self.losses[peer] += 1
        except KeyError:
            self.lg.debug(f"{self.id}: the unsupportive peer {peer} does not exist in {self.losses}")
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
        stderr.write(f" {colorama.Fore.RED}{lost_chunk_number}{colorama.Style.RESET_ALL}")

    def get_losser(self, lost_chunk_number):
        return self.destination_of_chunk[lost_chunk_number % (self.buffer_size)]

    def del_peer(self, peer_index):
        del self.team[peer_index]
        stderr.write(f" {colorama.Fore.BLUE}{peer_index}({len(self.team)}){colorama.Style.RESET_ALL}")
        stderr.write(f" {colorama.Fore.MAGENTA}{len(self.team)}{colorama.Style.RESET_ALL}")

    def remove_peer(self, peer):
        try:
            peer_index = self.team.index(peer)
        except ValueError:
            self.lg.debug(f"{self.id}: the removed peer {peer} does not exist in {self.peer_list}")
        else:
            self.del_peer(peer_index)

        try:
            del self.losses[peer]
        except KeyError:
            self.lg.debug(f"{self.id}: the removed peer {peer} does not exist in losses!")
        finally:
            pass

    def process_goodbye(self, peer):
        self.lg.debug(f"{self.id}: received [goodbye] from {peer}")
        if peer not in self.outgoing_peers_list:
            if peer in self.team:
                self.outgoing_peers_list.append(peer)
                self.lg.debug(f"{self.id}: {peer} marked for deletion")

    def say_goodbye(self, peer):
        msg = struct.pack("!i", Messages.GOODBYE)
        self.team_socket.sendto(msg, peer)
        self.lg.debug(f"{self.id}: sent [goodbye] to {peer}")
        
    def remove_outgoing_peers(self):
        if __debug__:
            if len(self.outgoing_peers_list) > 0:
                self.lg.debug(f"{self.id}: remove_outgoint_peers: len(outgoing_peers_list)={len(self.outgoing_peers_list)}\n")
        for p in self.outgoing_peers_list:
            self.say_goodbye(p)
            self.remove_peer(p)
            self.lg.debug(f"{self.id}: outgoing peer {p}")
        self.outgoing_peers_list.clear()

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
                stderr.write(f"{self.id}: unexpected message {packed_msg} with length={len(packed_msg)} received from {sender}")

            if msg[0] == Messages.GOODBYE:
                # Message sent by all peers when they leave the team
                self.process_goodbye(sender)

            elif msg[0] == Messages.LOST_CHUNK:
                # Message sent only by monitors when they lost a chunk
                lost_chunk_number = msg[1]
                self.process_lost_chunk(lost_chunk_number)
                self.lg.debug(f"{self.id}: received [lost chunk {msg[1]}] from {sender}")
                
            elif msg[0] == Messages.HELLO:
                # Message sent by peers to create a translation entry
                # in their NATs. No extra functionality by now.
                self.lg.info(f"{self.id}: received [hello] from {sender}")
            else:
                stderr.write(f"{self.id}: unexpected message {packed_msg} with length={len(packed_msg)} decoded as {msg} received from {sender}")

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

    def on_round_beginning(self):
        self.remove_outgoing_peers()
        #while not self.new_peers.empty():
        #    self.insert_peer(self.new_peers.get())
        #self.reset_counters()

    def run(self):
        chunk_number = 0
        total_peers = 0
        self.current_round = 0

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
                self.current_round += 1
                total_peers += len(self.team)
                self.on_round_beginning()
                stderr.write(f" {colorama.Fore.YELLOW}{self.current_round}{colorama.Style.RESET_ALL}")

            try:
                peer = self.team[self.peer_number]
            except IndexError:
                stderr.write(f"{self.id}: the peer with index {self.peer_number} does not exist. peers_list={self.team} peer_number={self.peer_number}")

            self.destination_of_chunk[chunk_number % (self.buffer_size)] = peer  # self.team.index(peer)
            self.send_chunk(chunk_number, chunk, peer)
            chunk_number = (chunk_number + 1) % Limits.MAX_CHUNK_NUMBER
            try:
                self.peer_number = (self.peer_number + 1) % len(self.team)
            except ZeroDivisionError:
                pass
            self.is_alive()

        # Say "goodbye" to the peers and wait for their "goodbye"s
        counter = 0
        while (len(self.team) > 0) and (counter < 10):
        #while len(self.team) > 0:
            self.lg.debug("{}: waiting for [goodbye]s from peers (peers_list={})".format(self.id, self.team))
            time.sleep(0.1)
            for p in self.team:
                self.say_goodbye(p)
            counter += 1

        #print("{}: total peers {} in {} rounds, {} peers/round".format(self.id, total_peers, self.current_round, (float)(total_peers)/(float)(self.current_round)))
        #print("{}: {} lost chunks of {}".format(self.id, self.total_lost_chunks, self.total_received_chunks, (float)(self.total_lost_chunks)/(float)(self.total_received_chunks)))
        #stderr.write(f"{self.id}: goodbye!\n")
