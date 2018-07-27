"""
@package p2psp-simulator
splitter_dbs module
"""

# DBS (Data Broadcasting Set) layer

# DBS is the most basic layer to provide communication among splitter
# (source of the stream) and peers (destination of the stream), using
# unicast transmissions. The splitter sends a different chunk of
# stream to each peer, using a random round-robin scheduler.

# TODO: In each round peers are selected at random, but all peers are
# sent a chunk, in a round).

from .common import Common
from threading import Thread
from threading import Lock
import time
from .simulator_stuff import Simulator_stuff
from .simulator_stuff import Simulator_socket as socket
# from .simulator_stuff import lg
import sys
import struct
import logging


class Splitter_DBS(Simulator_stuff):
    MAX_NUMBER_OF_LOST_CHUNKS = 32

    def __init__(self):

        #logging.basicConfig(format='%(MYVAR)s - %(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # lg.basicConfig(level=lg.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.lg = logging.getLogger(__name__)
        # handler = logging.StreamHandler()
        # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
        # formatter = logging.Formatter(fmt='splitter_dbs.py - %(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',datefmt='%H:%M:%S')
        # handler.setFormatter(formatter)
        # self.lg.addHandler(handler)
        self.lg.setLevel(logging.DEBUG)
        self.lg.critical('Critical messages enabled.')
        self.lg.error('Error messages enabled.')
        self.lg.warning('Warning message enabled.')
        self.lg.info('Informative message enabled.')
        self.lg.debug('Low-level debug message enabled.')

        self.id = "S"
        self.alive = True  # While True, keeps the splitter alive
        self.chunk_number = 0  # First chunk (number) to send
        self.peer_list = []  # Current peers in the team
        self.losses = {}  # (Detected) lost chunks per peer
        self.destination_of_chunk = []  # Destination peer of the buffered chunks
        self.buffer_size = Common.BUFFER_SIZE  # Buffer (of chunks) size
        self.peer_number = 0  # First peer to serve in the list of peers
        self.max_number_of_chunk_loss = self.MAX_NUMBER_OF_LOST_CHUNKS  # More lost, team removing
        self.number_of_monitors = 0  # Monitors report lost chunks
        self.outgoing_peer_list = []  # Peers which requested to leave the team

        # S I M U L A T I O N 
        self.current_round = 0  # Number of round (maybe not here).

        self.lg.info("{}: initialized".format(self.id))

    def setup_peer_connection_socket(self):
        self.peer_connection_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.peer_connection_socket.set_id(self.id)
        host = socket.gethostbyname(socket.gethostname())
        self.peer_connection_socket.bind((host,0))
        self.id = self.peer_connection_socket.getsockname()
        self.peer_connection_socket.listen(1)

    def setup_team_socket(self):
        self.team_socket = socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.team_socket.set_id(self.id)
        self.team_socket.bind(self.id)
        # self.team_socket.set_max_packet_size(struct.calcsize("is3s")) # Chunck index, chunk, origin

    def send_chunk(self, chunk_msg, peer):
        # self.lg.info("splitter_dbs.send_chunk({}, {})".format(chunk_msg, peer))
        msg = struct.pack("isli", *chunk_msg)
        # msg = struct.pack("is3s", chunk_msg[0], bytes(chunk_msg[1]), chunk_msg[2])
        self.team_socket.sendto(msg, peer)

    def receive_chunk(self):
        # Simulator_stuff.LOCK.acquire(True,0.1)
        time.sleep(0.05)  # Simulates bit-rate control
        # C -> Chunk, L -> Loss, G -> Goodbye, B -> Broken, P -> Peer, M -> Monitor, R -> Ready
        return b'C'

    def handle_arrivals(self):
        while self.alive:
            peer_serve_socket, peer = self.peer_connection_socket.accept()
            peer_serve_socket = socket(sock=peer_serve_socket)
            # peer_serve_socket.set_id(peer)
            self.lg.info("{}: connection from {}".format(self.id, peer))
            Thread(target=self.handle_a_peer_arrival, args=((peer_serve_socket, peer),)).start()

    def handle_a_peer_arrival(self, connection):

        serve_socket = connection[0]
        incoming_peer = connection[1]

        self.lg.info("{}: accepted connection from peer {}".format(self.id, incoming_peer))

        self.send_buffer_size(serve_socket)
        self.send_the_number_of_peers(serve_socket)
        self.send_the_list_of_peers(serve_socket)

        self.lg.info("{}: waiting for incoming peer".format(self.id))

        msg_length = struct.calcsize("s")
        msg = serve_socket.recv(msg_length)
        message = struct.unpack("s", msg)[0]
        self.lg.info("{}: received {} from {}".format(self.id, message, incoming_peer))

        self.insert_peer(incoming_peer)
        # ------------------
        # ---- Only for simulation purposes. Unknown in real implementation -----
        msg = serve_socket.recv(struct.calcsize('H'))
        ptype = struct.unpack('H', msg)
        ptype = ptype[0]
        if (ptype == 0):
            self.number_of_monitors += 1
            if Simulator_stuff.FEEDBACK:
                Simulator_stuff.FEEDBACK["DRAW"].put(("MAP",','.join(map(str,incoming_peer)),"M"))
        
        # S I M U L A T I O N
        if Simulator_stuff.FEEDBACK:
            Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str,incoming_peer))))
        self.lg.info("{}: number of monitors = {}".format(self.id, self.number_of_monitors))

        serve_socket.close()

    def send_buffer_size(self, peer_serve_socket):
        self.lg.info("{}: buffer size = {}".format(self.id, self.buffer_size))
        # peer_serve_socket.sendall(self.buffer_size, "H")
        msg = struct.pack("H", self.buffer_size)
        peer_serve_socket.sendall(msg)

    def send_the_number_of_peers(self, peer_serve_socket):
        self.lg.info("{}: sending number of monitors = {}".format(self.id, self.number_of_monitors))
        # peer_serve_socket.sendall(self.number_of_monitors, "H")
        msg = struct.pack("H", self.number_of_monitors)
        peer_serve_socket.sendall(msg)
        self.lg.info("{}: sending list of peers of length = {}".format(self.id, len(self.peer_list)))
        # peer_serve_socket.sendall(len(self.peer_list), "H")
        msg = struct.pack("H", len(self.peer_list))
        peer_serve_socket.sendall(msg)

    def send_the_list_of_peers(self, peer_serve_socket):
        self.lg.info("{}: sending peer list = {}".format(self.id, self.peer_list))
        for p in self.peer_list:
            # peer_serve_socket.sendall(p, "6s")
            msg = struct.pack("li",socket.ip2int(p[0]),p[1])
            peer_serve_socket.sendall(msg)

    def insert_peer(self, peer):
        if peer not in self.peer_list:
            self.peer_list.append(peer)
        self.losses[peer] = 0
        self.lg.info("{}: {} inserted in the team".format(self.id, peer))

    def increment_unsupportivity_of_peer(self, peer):
        try:
            self.losses[peer] += 1
        except KeyError:
            self.lg.error("{}: unexpected error, the unsupportive peer {} does not exist!".format(peer))
        else:
            self.lg.info("{}: peer {} has lost {} chunks".format(self.id, peer, self.losses[peer]))
            if self.losses[peer] > Common.MAX_CHUNK_LOSS:
                self.lg.info("{}: {} removed".format(self.id, peer))
                self.remove_peer(peer)
        finally:
            pass

    def process_lost_chunk(self, lost_chunk_number, sender):
        destination = self.get_losser(lost_chunk_number)
        self.lg.info(
            "{}: sender {} complains about lost chunk {} with destination {}".format(self.id, sender, lost_chunk_number,
                                                                                     destination))
        self.increment_unsupportivity_of_peer(destination)

    # def get_lost_chunk_number(self, message):
    #    return message[1]

    def get_losser(self, lost_chunk_number):
        return self.destination_of_chunk[lost_chunk_number % self.buffer_size]

    def remove_peer(self, peer):
        try:
            self.peer_list.remove(peer)
        except ValueError:
            self.lg.error("{}: unexpected error, the removed peer {} does not exist!".format(self.id, peer))
        else:
            # self.peer_number -= 1
            # S I M U L A T I O N
            if Simulator_stuff.FEEDBACK:
                Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "OUT", ','.join(map(str,peer))))
            if peer[0] == "M" and peer[1] != "P":
                self.number_of_monitors -= 1

        try:
            del self.losses[peer]
        except KeyError:
            self.lg.error("{}: unexpected error, the removed peer {} does not exist in losses".format(self.id, peer))
        finally:
            pass

    def process_goodbye(self, peer):
        self.lg.info("{}: received [goodbye] from".format(self.id, peer))
        if peer not in self.outgoing_peer_list:
            if peer in self.peer_list:
                self.outgoing_peer_list.append(peer)
                self.lg.info("{}: marked for deletion".format(self.id, peer))

    def say_goodbye(self, peer):
        # self.team_socket.sendto(Common.GOODBYE, "i" , peer)
        msg = struct.pack("i", Common.GOODBYE)
        self.team_socket.sendto(msg, peer)

    def remove_outgoing_peers(self):
        for p in self.outgoing_peer_list:
            self.say_goodbye(p)
            self.remove_peer(p)
        self.outgoing_peer_list.clear()

    def on_round_beginning(self):
        self.remove_outgoing_peers()

    def moderate_the_team(self):
        while self.alive:
            # message, sender = self.team_socket.recvfrom()
            msg, sender = self.team_socket.recvfrom(100)
            if len(msg) == 2:
                # msg = struct.unpack("i", packed_msg)
                self.process_goodbye(sender)
            else:
                lost_chunk_number = struct.unpack("ii", msg)[1]
                # lost_chunk_number = self.get_lost_chunk_number(message)
                self.process_lost_chunk(lost_chunk_number, sender)

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

    def get_id(self):
        return self.id

    def run(self):

        Thread(target=self.handle_arrivals).start()
        Thread(target=self.moderate_the_team).start()
        Thread(target=self.reset_counters_thread).start()

        while len(self.peer_list) == 0:
            print(".")
            time.sleep(0.1)

        while self.alive:

            chunk = self.receive_chunk()

            # ????
            self.lg.info("peer_number = {}".format(self.peer_number))
            print("peer_number = {}".format(self.peer_number))
            if self.peer_number == 0:
                self.on_round_beginning()  # Remove outgoing peers

                # S I M U L A T I O N
                self.lg.info("{}: current round {}".format(self.id, self.current_round))
                if Simulator_stuff.FEEDBACK:
                    Simulator_stuff.FEEDBACK["STATUS"].put(("R", self.current_round))
                    Simulator_stuff.FEEDBACK["DRAW"].put(("R", self.current_round))
                    Simulator_stuff.FEEDBACK["DRAW"].put(("T", "M", self.number_of_monitors, self.current_round))
                    Simulator_stuff.FEEDBACK["DRAW"].put(
                     ("T", "P", (len(self.peer_list) - self.number_of_monitors), self.current_round))

            # try:
            peer = self.peer_list[self.peer_number]
            # except IndexError:
            # lg.error("peer_list={} peer_number={}".format(self.peer_list, self.peer_number))
            # raise
            message = (self.chunk_number, chunk, socket.ip2int(peer[0]),peer[1])
            self.destination_of_chunk.insert(self.chunk_number % self.buffer_size, peer)
            #            try:
            self.send_chunk(message, peer)
            self.chunk_number = (self.chunk_number + 1) % Common.MAX_CHUNK_NUMBER
            self.compute_next_peer_number(peer)

            #            except IndexError:
            #                self.lg.error("{}: the monitor peer has died!".format(self.id))
            #                self.lg.error("{}: peer_list = {}".format(self.id, self.peer_list))
            #                self.lg.error("{}: peer_number = {}".format(self.id, self.peer_number))

            # S I M U L A T I O N
            if self.peer_number == 0:
                self.current_round += 1
                #self.lg.info("round = {}".format(self.current_round))
