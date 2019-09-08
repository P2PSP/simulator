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
from .common import Common
from .simulator_stuff import Simulator_socket as socket
from .ip_tools import IP_tools

# class Splitter_DBS(Simulator_stuff):


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
        self.peer_list = []  # Current peers in the team
        self.losses = {}  # (Detected) lost chunks per peer
        self.destination_of_chunk = (buffer_size*2)*[0]
        #self.destination_of_chunk = {}
        self.peer_number = 0  # First peer to serve in the list of peers
        self.number_of_monitors = 0  # Monitors report lost chunks
        self.outgoing_peer_list = []  # Peers which requested to leave the team

        self.chunk_packet_format = "!isIi"

        self.current_round = 0  # Number of round (maybe not here).

        self.lg.debug("Splitter_DBS: initialized")

    def setup_peer_connection_socket(self, port=0):
        self.peer_connection_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peer_connection_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # self.peer_connection_socket.set_id(self.id)
        host = socket.gethostbyname(socket.gethostname())
        self.peer_connection_socket.bind(('', port))
        self.id = self.peer_connection_socket.getsockname()
        print("{}: I'm the splitter".format(self.id))
        self.peer_connection_socket.listen(1)

    def setup_team_socket(self):
        self.team_socket = socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.team_socket.set_id(self.id)
        self.team_socket.bind(self.id)
        # self.team_socket.set_max_packet_size(struct.calcsize("is3s")) # Chunck index, chunk, origin

    def send_chunk(self, chunk_msg, peer):
        # self.lg.info("splitter_dbs.send_chunk({}, {})".format(chunk_msg, peer))
        #msg = struct.pack("isli", *chunk_msg)
        # msg = struct.pack("is3s", chunk_msg[0], bytes(chunk_msg[1]), chunk_msg[2])
        self.team_socket.sendto(chunk_msg, peer)
        self.lg.debug("{}: chunk {} sent to {}".format(self.id, chunk_msg[0], peer))

    def handle_arrivals(self):
        while self.alive:
            peer_serve_socket, peer = self.peer_connection_socket.accept()
            peer_serve_socket = socket(sock=peer_serve_socket)
            # peer_serve_socket.set_id(peer)
            self.lg.info("{}: connection from {}".format(self.id, peer))
            Thread(target=self.handle_a_peer_arrival, args=((peer_serve_socket, peer),)).start()

    # def send_the_header(self):
    #    pass

    def send_the_chunk_size(self, peer_serve_socket):
        pass

    def send_header_bytes(self, peer_serve_socket):
        pass

    def handle_a_peer_arrival(self, connection):

        serve_socket = connection[0]
        incoming_peer = connection[1]

        print("{}: accepted connection from peer {}" .format(self.id, incoming_peer))

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
        self.lg.debug("{}: peer public endpint={}".format(self.id, endpoint))
        # peer_serve_socket.sendall(Splitter_DBS.buffer_size, "H")
        msg = struct.pack("!Ii", IP_tools.ip2int(endpoint[0]), endpoint[1])
        peer_serve_socket.sendall(msg)

    def send_buffer_size(self, peer_serve_socket):
        # peer_serve_socket.sendall(Splitter_DBS.buffer_size, "H")
        msg = struct.pack("!H", self.buffer_size)
        peer_serve_socket.sendall(msg)

    def send_the_number_of_peers(self, peer_serve_socket):
        self.lg.debug("{}: sending number_of_monitors={}".format(self.id, self.number_of_monitors))
        # peer_serve_socket.sendall(self.number_of_monitors, "H")
        msg = struct.pack("!H", self.number_of_monitors)
        peer_serve_socket.sendall(msg)
        self.lg.debug("{}: sending list of peers of length={}".format(self.id, len(self.peer_list)))
        # peer_serve_socket.sendall(len(self.peer_list), "H")
        msg = struct.pack("!H", len(self.peer_list))
        peer_serve_socket.sendall(msg)

    def send_the_list_of_peers(self, peer_serve_socket):
        self.lg.debug("{}: sending peer_list={}".format(self.id, self.peer_list))
        for p in self.peer_list:
            # peer_serve_socket.sendall(p, "6s")
            msg = struct.pack("!Ii", IP_tools.ip2int(p[0]), p[1])
            peer_serve_socket.sendall(msg)

    def insert_peer(self, peer):
        if peer not in self.peer_list:
            self.peer_list.append(peer)
        self.losses[peer] = 0
        self.lg.debug("{}: {} inserted in the team".format(self.id, peer))

    def increment_unsupportivity_of_peer(self, peer):

#        try:
#            peer_index = self.losses.index(peer)
#        except ValueError:
#            self.lg.warning(f"{self.id}: the removed peer does not exist in {self.losses}")
#        else:
#            self.losses[peer] += 1
#            self.lg.info(f"{self.id}: peer {peer} has lost {self.losses[peer]} chunks")
#            sys.stderr.write(f" {self.losses[peer]}/{self.max_chunk_loss} ")
#            if self.losses[peer] > 1:#self.max_chunk_loss:
#                self.remove_peer(peer)
        
        try:
            #self.losses[peer] += 1/self.max_chunk_loss
            self.losses[peer] += 1
        except KeyError:
            self.lg.warning(f"{self.id}: the unsupportive peer {peer} does not exist in {self.losses}")
        else:
            self.lg.info(f"{self.id}: peer {peer} has lost {self.losses[peer]} chunks")
#            sys.stderr.write(f" {self.losses[peer]}/{self.max_chunk_loss} ")
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

    def remove_peer(self, peer):
        self.lg.info(f"{self.id}: peer {peer} removed")
        try:
            self.peer_list.remove(peer)
        except ValueError:
            self.lg.warning(f"{self.id}: the removed peer {peer} does not exist in peers_list!")

        try:
            del self.losses[peer]
        except KeyError:
            self.lg.warning(f"{self.id}: the removed peer {peer} does not exist in losses!")
        finally:
            pass

    def process_goodbye(self, peer):
        self.lg.debug("{}: received [goodbye] from {}".format(self.id, peer))
        if peer not in self.outgoing_peer_list:
            if peer in self.peer_list:
                self.outgoing_peer_list.append(peer)
                self.lg.debug("{}: marked for deletion".format(self.id, peer))

    def say_goodbye(self, peer):
        # self.team_socket.sendto(Messages.GOODBYE, "i" , peer)
        msg = struct.pack("!i", Messages.GOODBYE)
        self.team_socket.sendto(msg, peer)
        self.lg.debug("{}: sent [goodbye] to {}".format(self.id, peer))

    def remove_outgoing_peers(self):
        for p in self.outgoing_peer_list:
            self.say_goodbye(p)
            self.remove_peer(p)
            self.lg.debug("{}: outgoing peer {}".format(self.id, p))
        self.outgoing_peer_list.clear()

    def on_round_beginning(self):
        self.remove_outgoing_peers()
        self.reset_counters()

    def moderate_the_team(self):
        while self.alive:
            # message, sender = self.team_socket.recvfrom()
            packed_msg, sender = self.team_socket.recvfrom(100)
            #print("{}: packet={}".format(self.id, packed_msg))
            if len(packed_msg) == struct.calcsize("!iii"):
                msg = struct.unpack("!iii", packed_msg)
                if msg[0] == Messages.GOODBYE:
                    # Message sent by all peers when they leave the team
                    self.process_goodbye(sender)
                    if self.lost_chunks_from[sender] == 0:
                        self.received_chunks_from[sender] = msg[1]
                        self.lost_chunks_from[sender] = msg[2]
                        self.total_received_chunks += self.received_chunks_from[sender]
                        self.total_lost_chunks += self.lost_chunks_from[sender]
                    self.lg.debug("{}: received [goodbye {} {}] from {}".format(self.id, msg[1], msg[2], sender))
                    self.lg.debug("{}: received_chunks_from[{}]={}".format(
                        self.id, sender, self.received_chunks_from[sender]))
                    self.lg.debug("{}: lost_chunks_from[{}]={}".format(self.id, sender, self.lost_chunks_from[sender]))
                    self.lg.debug("{}: total_received_chunks={}".format(self.id, self.total_received_chunks))
                    self.lg.debug("{}: total_lost_chunks={}".format(self.id, self.total_lost_chunks))
            elif len(packed_msg) == struct.calcsize("!ii"):
                msg = struct.unpack("!ii", packed_msg)
                if msg[0] == Messages.LOST_CHUNK:
                    # Message sent only by monitors when they lost a chunk
                    lost_chunk_number = msg[1]
                    # lost_chunk_number = self.get_lost_chunk_number(message)
                    self.process_lost_chunk(lost_chunk_number, sender)
                    self.lg.debug("{}: received [lost chunk {}] from {}".format(self.id, msg[1], sender))
            else:
                self.lg.warning("{}: received unexpected message {} from {}".format(self.id, packed_msg, sender))

    #def reset_counters_thread(self):
    #    while self.alive:
    #        self.reset_counters()
    #        time.sleep(Common.COUNTERS_TIMING)

    def compute_next_peer_number(self, peer):
        try:
            self.peer_number = (self.peer_number + 1) % len(self.peer_list)
        except ZeroDivisionError:
            pass

    def start(self):
        Thread(target=self.run).start()

    def get_id(self):
        return self.id

    def compose_chunk_packet(self, chunk, peer):
        chunk_msg = (self.chunk_number, chunk, IP_tools.ip2int(peer[0]), peer[1])
        msg = struct.pack(self.chunk_packet_format, *chunk_msg)
        return msg

    def run(self):
        self.received_chunks_from = {}
        self.lost_chunks_from = {}
        self.total_received_chunks = 0
        self.total_lost_chunks = 0
        total_peers = 0

        Thread(target=self.handle_arrivals).start()
        Thread(target=self.moderate_the_team).start()
        #Thread(target=self.reset_counters_thread).start()

        while len(self.peer_list) == 0:
            print("{}: waiting for a monitor")
            time.sleep(1)
        print()

        while len(self.peer_list) > 0:

            chunk = self.receive_chunk()

            if self.peer_number == 0:
                total_peers += len(self.peer_list)
                self.on_round_beginning()  # Remove outgoing peers

            try:
                peer = self.peer_list[self.peer_number]
            except IndexError:
                self.lg.warning("{}: the peer with index {} does not exist. peer_list={} peer_number={}".format(
                    self.id, self.peer_number, self.peer_list, self.peer_number))
                # raise

            message = self.compose_chunk_packet(chunk, peer)
            self.destination_of_chunk[self.chunk_number % (self.buffer_size*2)] = peer
            # if __debug__:
            #    self.lg.debug("{}: showing destination_of_chunk:".format(self.id))
            #    counter = 0
            #    for i in self.destination_of_chunk:
            #        self.lg.debug("{} -> {}".format(counter, i))
            #        counter += 1
            #            try:
            self.send_chunk(message, peer)
            self.chunk_number = (self.chunk_number + 1) % Common.MAX_CHUNK_NUMBER
            try:
                self.peer_number = (self.peer_number + 1) % len(self.peer_list)
            except ZeroDivisionError:
                pass

        self.alive = False
        self.lg.debug("{}: alive = {}".format(self.id, self.alive))

        print("{}: total peers {} in {} rounds, {} peers/round"
              .format(self.id, total_peers, self.current_round, (float)(total_peers)/(float)(self.current_round)))
        #print("{}: {} lost chunks of {}".format(self.id, self.total_lost_chunks, self.total_received_chunks, (float)(self.total_lost_chunks)/(float)(self.total_received_chunks)))
        print("{}: {} lost chunks of {}".format(self.id, self.total_lost_chunks, self.total_received_chunks))
