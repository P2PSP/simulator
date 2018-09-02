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
# from threading import Lock
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
        # self.lg.setLevel(logging.DEBUG)
        self.lg.setLevel(Simulator_stuff.loglevel)
        # self.lg.critical('Critical messages enabled.')
        # self.lg.error('Error messages enabled.')
        # self.lg.warning('Warning message enabled.')
        # self.lg.info('Informative message enabled.')
        # self.lg.debug('Low-level debug message enabled.')

        self.id = "S"
        self.alive = True  # While True, keeps the splitter alive
        self.chunk_number = 0  # First chunk (number) to send
        self.peer_list = []  # Current peers in the team
        self.losses = {}  # (Detected) lost chunks per peer
        self.buffer_size = Common.BUFFER_SIZE  # Buffer (of chunks) size
        self.destination_of_chunk = self.buffer_size*[0]  # Destination peer of the buffered chunks
        self.peer_number = 0  # First peer to serve in the list of peers
        self.max_number_of_chunk_loss = self.MAX_NUMBER_OF_LOST_CHUNKS  # More lost, team removing
        self.number_of_monitors = 0  # Monitors report lost chunks
        self.outgoing_peer_list = []  # Peers which requested to leave the team

        # S I M U L A T I O N 
        self.current_round = 0  # Number of round (maybe not here).
        self.max_number_of_rounds = 10

        self.lg.debug("{}: initialized".format(self.id))

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
        self.lg.debug("{}: chunk {} sent to {}".format(self.id, chunk_msg[0], peer))

    def receive_chunk(self):
        # Simulator_stuff.LOCK.acquire(True,0.1)
        time.sleep(Common.CHUNK_CADENCE)  # Simulates bit-rate control
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

        self.lg.debug("{}: accepted connection from peer {}".format(self.id, incoming_peer))

        self.send_buffer_size(serve_socket)
        self.send_the_number_of_peers(serve_socket)
        self.send_the_list_of_peers(serve_socket)

        self.lg.debug("{}: waiting for incoming peer".format(self.id))

        msg_length = struct.calcsize("s")
        msg = serve_socket.recv(msg_length)
        message = struct.unpack("s", msg)[0]
        self.lg.debug("{}: received {} from {}".format(self.id, message, incoming_peer))

        self.insert_peer(incoming_peer)
        # ------------------
        # ---- Only for simulation purposes. Unknown in real implementation -----
        self.lost_chunks_from[incoming_peer] = 0
        self.received_chunks_from[incoming_peer] = 0
        msg = serve_socket.recv(struct.calcsize('H'))
        ptype = struct.unpack('H', msg)
        ptype = ptype[0]
        if (ptype == 0):
            self.number_of_monitors += 1
            # if Simulator_stuff.FEEDBACK:
                # Simulator_stuff.FEEDBACK["DRAW"].put(("MAP",','.join(map(str,incoming_peer)),"M"))
        
        # S I M U L A T I O N
        if Simulator_stuff.FEEDBACK:
            Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str,incoming_peer))))
        self.lg.debug("{}: number of monitors = {}".format(self.id, self.number_of_monitors))

        serve_socket.close()

    def send_buffer_size(self, peer_serve_socket):
        self.lg.debug("{}: buffer_size={}".format(self.id, self.buffer_size))
        # peer_serve_socket.sendall(self.buffer_size, "H")
        msg = struct.pack("H", self.buffer_size)
        peer_serve_socket.sendall(msg)

    def send_the_number_of_peers(self, peer_serve_socket):
        self.lg.debug("{}: sending number_of_monitors={}".format(self.id, self.number_of_monitors))
        # peer_serve_socket.sendall(self.number_of_monitors, "H")
        msg = struct.pack("H", self.number_of_monitors)
        peer_serve_socket.sendall(msg)
        self.lg.debug("{}: sending list of peers of length = {}".format(self.id, len(self.peer_list)))
        # peer_serve_socket.sendall(len(self.peer_list), "H")
        msg = struct.pack("H", len(self.peer_list))
        peer_serve_socket.sendall(msg)

    def send_the_list_of_peers(self, peer_serve_socket):
        self.lg.debug("{}: sending peer_list={}".format(self.id, self.peer_list))
        for p in self.peer_list:
            # peer_serve_socket.sendall(p, "6s")
            msg = struct.pack("li",socket.ip2int(p[0]),p[1])
            peer_serve_socket.sendall(msg)

    def insert_peer(self, peer):
        if peer not in self.peer_list:
            self.peer_list.append(peer)
        self.losses[peer] = 0
        self.lg.debug("{}: {} inserted in the team".format(self.id, peer))

    def increment_unsupportivity_of_peer(self, peer):
        try:
            self.losses[peer] += 1
        except KeyError:
            self.lg.warning("{}: the unsupportive peer {} does not exist".format(self.id, peer))
        else:
            self.lg.info("{}: peer {} has lost {} chunks".format(self.id, peer, self.losses[peer]))
            if self.losses[peer] > Common.MAX_CHUNK_LOSS:
                self.remove_peer(peer)
        finally:
            pass

    def process_lost_chunk(self, lost_chunk_number, sender):
        destination = self.get_losser(lost_chunk_number)
        self.lg.debug("{}: sender {} complains about lost chunk {} with destination {}".format(self.id, sender, lost_chunk_number, destination))
        self.increment_unsupportivity_of_peer(destination)

    # def get_lost_chunk_number(self, message):
    #    return message[1]

    def get_losser(self, lost_chunk_number):
        return self.destination_of_chunk[lost_chunk_number % self.buffer_size]

    def remove_peer(self, peer):
        try:
            self.peer_list.remove(peer)
            self.lg.debug("{}: peer {} removed".format(self.id, peer))
        except ValueError:
            self.lg.warning("{}: the removed peer {} does not exist!".format(self.id, peer))
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
            self.lg.warning("{}: the removed peer {} does not exist in losses".format(self.id, peer))
        finally:
            pass

    def remove_peer_old(self, peer):
        if peer in self.peer_list:
            self.peer_list.remove(peer)
        # self.peer_number -= 1
        # S I M U L A T I O N
        if Simulator_stuff.FEEDBACK:
            Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "OUT", ','.join(map(str,peer))))
        if peer[0] == "M" and peer[1] != "P":
            self.number_of_monitors -= 1

        if peer in self.losses:
            del self.losses[peer]

    def process_goodbye(self, peer):
        if peer not in self.outgoing_peer_list:
            if peer in self.peer_list:
                self.outgoing_peer_list.append(peer)
                self.lg.debug("{}: marked for deletion".format(self.id, peer))

    def say_goodbye(self, peer):
        # self.team_socket.sendto(Common.GOODBYE, "i" , peer)
        msg = struct.pack("i", Common.GOODBYE)
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

    def moderate_the_team(self):
        while self.alive:
            # message, sender = self.team_socket.recvfrom()
            packed_msg, sender = self.team_socket.recvfrom(100)
            if len(packed_msg) == struct.calcsize("iii"):
                msg = struct.unpack("iii", packed_msg)
                if msg[0] == Common.GOODBYE:
                    # Message sent by all peers when they leave the team
                    self.process_goodbye(sender)
                    if self.lost_chunks_from[sender] == 0:
                        self.received_chunks_from[sender] = msg[1]
                        self.lost_chunks_from[sender] = msg[2]
                        self.total_received_chunks += self.received_chunks_from[sender]
                        self.total_lost_chunks += self.lost_chunks_from[sender]
                    self.lg.debug("{}: received [goodbye {} {}] from {}".format(self.id, msg[1], msg[2], sender))
                    self.lg.debug("{}: received_chunks_from[{}]={}".format(self.id, sender, self.received_chunks_from[sender]))
                    self.lg.debug("{}: lost_chunks_from[{}] = {}".format(self.id, sender, self.lost_chunks_from[sender]))
                    self.lg.debug("{}: total_received_chunks={}".format(self.id, self.total_received_chunks))
                    self.lg.debug("{}: total_lost_chunks={}".format(self.id, self.total_lost_chunks))
            elif len(packed_msg) == struct.calcsize("ii"):
                msg = struct.unpack("ii", packed_msg)
                if msg[0] == Common.LOST_CHUNK:
                    # Message sent only by monitors when they lost a chunk
                    lost_chunk_number = msg[1]
                    # lost_chunk_number = self.get_lost_chunk_number(message)
                    self.process_lost_chunk(lost_chunk_number, sender)
                    self.lg.debug("{}: received [lost chunk {}] from {}".format(self.id, msg[1], sender))
            else:
                self.lg.warning("{}: received unexpected message".format(self.id))

    def reset_counters(self):
        for i in self.losses:
            self.losses[i] /= 2

    def reset_counters_thread(self):
        while self.alive:
            self.reset_counters()
            time.sleep(Common.COUNTERS_TIMING)

    def compute_next_peer_number(self, peer):
        try:
            self.peer_number = (self.peer_number + 1) % len(self.peer_list)
        except ZeroDivisionError:
            pass

    def start(self):
        Thread(target=self.run).start()

    def get_id(self):
        return self.id

    def run(self):

        chunk_counter = 0
        self.received_chunks_from = {}
        self.lost_chunks_from = {}
        self.total_received_chunks = 0
        self.total_lost_chunks = 0

        Thread(target=self.handle_arrivals).start()
        Thread(target=self.moderate_the_team).start()
        Thread(target=self.reset_counters_thread).start()

        while len(self.peer_list) == 0:
            print(".", end=' ')
            time.sleep(0.1)
        print()

        #while self.alive:
        while self.current_round < self.max_number_of_rounds:

            chunk = self.receive_chunk()
            chunk_counter += 1

            # ????
            #self.lg.info("peer_number = {}".format(self.peer_number))
            #print("peer_number = {}".format(self.peer_number))
            if self.peer_number == 0:
                self.on_round_beginning()  # Remove outgoing peers

                # S I M U L A T I O N
                if Simulator_stuff.FEEDBACK:
                    Simulator_stuff.FEEDBACK["STATUS"].put(("R", self.current_round))
                    Simulator_stuff.FEEDBACK["DRAW"].put(("R", self.current_round))
                    Simulator_stuff.FEEDBACK["DRAW"].put(("T", "M", self.number_of_monitors, self.current_round))
                    Simulator_stuff.FEEDBACK["DRAW"].put(("T", "P", (len(self.peer_list) - self.number_of_monitors), self.current_round))

            try:
                peer = self.peer_list[self.peer_number]
            except IndexError:
                self.lg.warning("{}: the peer with index {} does not exist. peer_list={} peer_number={}".format(self.id, self.peer_number, self.peer_list, self.peer_number))
                # raise
            
            message = (self.chunk_number, chunk, socket.ip2int(peer[0]),peer[1])
            self.destination_of_chunk[self.chunk_number % self.buffer_size] = peer
            if __debug__:
                self.lg.debug("{}: showing destination_of_chunk:".format(self.id))
                counter = 0
                for i in self.destination_of_chunk:
                    self.lg.debug("{} -> {}".format(counter, i))
                    counter += 1
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
                self.lg.info("{}: round={:03} chunk_number={:05} number_of_peers={:03}".format(self.id, self.current_round, self.chunk_number, len(self.peer_list)))
                self.lg.debug("{}: peer_list={}".format(self.id, self.peer_list))
                sys.stderr.write(str(self.current_round)+"/"+str(self.max_number_of_rounds)+"\r")
                if __debug__:
                    for peer,loss in self.losses.items():
                        if loss>0:
                            self.lg.debug("{}:{}".format(peer,loss))

        self.alive = False
        self.lg.debug("{}: alive = {}".format(self.id, self.alive))

        counter = 0
        while (len(self.peer_list) > 0) and (counter < 10):
            self.lg.info("{}: peer_list={}".format(self.id, self.peer_list))
            time.sleep(0.1)
            for p in self.peer_list:
                self.say_goodbye(p)
            if Simulator_stuff.FEEDBACK:
                Simulator_stuff.FEEDBACK["STATUS"].put(("Bye", "Bye"))
                self.lg.debug("{}: Bye sent to simulator".format(self.id))
            counter += 1

        print("{}: {} lost chunks of {}".format(self.id, self.total_lost_chunks, self.total_received_chunks))
