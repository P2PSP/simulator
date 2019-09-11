"""
@package simulator
peer_dbs module
"""

# TODO: remove self.number_of_peers (it is the length of self.team).
# TODO: the splitter receives the chunk 0 from the monitor.

# Abstract class

# DBS (Data Broadcasting Set) layer, peer side.

# DBS peers receive chunks from the splitter and other peers, and
# resend them, depending on the forwarding requests performed by the
# peers. In a nutshell, if a peer X wants to receive from peer Y
# the chunks from origin Z, X must request it to Y, explicitally.

import logging
import struct
import sys
import time
from threading import Thread

#import netifaces

from .messages import Messages
from .limits import Limits
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .ip_tools import IP_tools
from .chunk_structure import ChunkStructure

import random

class Peer_DBS():

    peer_port = 4553
    splitter = ("localhost", 4552)

    def __init__(self, id, name, loglevel):

        self.lg = logging.getLogger(name)
        self.lg.setLevel(loglevel)

        # Peer identification. Depending on the simulation accuracy, it
        # can be a simple string or an (local) endpoint.
        #self.id = None

        self.public_endpoint = (None, 0)
        
        # S I M U L A T I O N
        self._id = id

        # Chunk currently played.
        self.chunk_to_play = 0

        # Buffer of chunks (used as a circular queue).
        self.chunks = []

        # While True, keeps the peer alive.
        self.player_connected = True

        # Number of monitors in the team (information sent by the
        # splitter but unsed at this level, maybe it could be placed
        # in a different file ...).
        #self.number_of_monitors = 0

        # To ensure an outgoing peer will not receive a chunk from the
        # splitter, the outgoing peer must wait for the goodbye from
        # the splitter before leaving the team.
        self.waiting_for_goodbye = True

        # NOTE: Only a monitor peer should know if it is a
        # monitor. The splitter could send to the incoming peer a
        # boolean telling it if it is a monitor.

        # A flag that when True, fires the leaving process.
        self.ready_to_leave_the_team = False

        # Forwarding rules of chunks, indexed by origins. If a peer
        # has an entry forward[Y]=[A, B, C], every chunk received
        # from origin (endpoint) Y will be forwarded towards
        # peers A, B and C.
        self.forward = {}

        # List of pending chunks (numbers) to be sent to peers. Por
        # example, if pending[X] = [1,5,7], the chunks stored in
        # entries 1, 5, and 7 of the buffer will be sent to the peer
        # X, in a burst, when a chunk arrives. The number of entries
        # (keys) in pending{} is the fan-out of the peer.
        self.pending = {}

        # Peers (end-points) in the known team, which is formed by
        # those peers that has sent to this peer a chunk, directly or
        # indirectly.
        self.team = []

        # Sent and received chunks.
        self.sendto_counter = 0  # Unused

        # S I M U L A T I O N
        self.received_chunks = 0

        # The longest message expected to be received: chunk_number,
        # chunk, IP address of the origin peer, and port of the origin
        # peer.
        self.chunk_packet_format = "!isIi"
        self.max_packet_length = struct.calcsize(self.chunk_packet_format)
        self.lg.info(f"{self.public_endpoint}: max_packet_length={self.max_packet_length}")

        self.neighbor_index = 0

        # Played or lost
        self.number_of_chunks_consumed = 0

        # S I M U L A T I O N
        self.number_of_lost_chunks = 0

        # S I M U L A T I O N
        self.played = 0

        # S I M U L A T I O N
        #self.link_failure_prob = 0.0

        if __debug__:
            self.rounds_counter = 0

#        self.rounds_counter = 0

        if __debug__:
            self.prev_chunk_number = 0  # Jitter in chunks-time
            self.prev_chunk_number_round = 0

        self.alive = {}  # True if received a chunk in the last round from that origin
#        self.debts = {}
#        self.max_debt = 8
        self.name = name
        self.lg.info(f"{name} {self.public_endpoint}: DBS initialized")

    def set_splitter(self, splitter):
        self.splitter = splitter

    def listen_to_the_team(self):
        self.team_socket = socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, loglevel=self.lg.level)
        self.team_socket.bind(self.public_endpoint)
        self.lg.info(f"{self.ext_id}: listening to the team")
        self.say_hello(self.splitter) # Only works for cone NATs
        #self.team_socket.bind(("", self.public_endpoint[1]))
        #self.team_socket.settimeout(self.timeout) # In seconds
        #self.team_socket.setblocking(0)

    def receive_public_endpoint(self):
        msg_length = struct.calcsize("!Ii")
        msg = self.splitter_socket.recv(msg_length)
        pe = struct.unpack("!Ii", msg)
        self.public_endpoint = (IP_tools.int2ip(pe[0]), pe[1])
        #self.id = self.public_endpoint
        self.lg.info(f"{self.public_endpoint}: received public_endpoint")

        self.ext_id = ("%03d" % self.peer_index_in_team, self.public_endpoint[0], int("%5d" % self.public_endpoint[1]))
        self.lg.info(f"{self.ext_id}: peer_index_in_team={self.peer_index_in_team}")
        #sys.stderr.write(f"{self.name} {self.ext_id} alive :-)\n")
        #sys.stderr.flush()

    def receive_buffer_size(self):
        # self.buffer_size = self.splitter_socket.recv("H")
        # self.buffer_size = self.recv("H")
        msg_length = struct.calcsize("!H")
        msg = self.splitter_socket.recv(msg_length)
        self.buffer_size = struct.unpack("!H", msg)[0]
        self.lg.info(f"{self.ext_id}: buffer_size={self.buffer_size}")
#        self.optimization_horizon = int(self.buffer_size*0.1)
        #self.optimization_horizon = 0
        
    def receive_the_number_of_peers(self):
        msg_length = struct.calcsize("!H")
        msg = self.splitter_socket.recv(msg_length)
        self.number_of_peers = struct.unpack("!H", msg)[0]
        self.lg.info(f"{self.ext_id}: number_of_peers={self.number_of_peers}")

    def receive_peer_index_in_team(self):
        msg_length = struct.calcsize("!H")
        msg = self.splitter_socket.recv(msg_length)
        self.peer_index_in_team = struct.unpack("!H", msg)[0]
        self.lg.info(f"{self.public_endpoint}: peer_index_in_team={self.peer_index_in_team}")

    def say_hello(self, entity):
        msg = struct.pack("!i", Messages.HELLO)
        self.team_socket.sendto(msg, entity)
        self.lg.info(f"{self.ext_id}: sent [hello] to {entity}")

    def receive_the_list_of_peers(self):
#        self.index_of_peer = {}
        peers_pending_of_reception = self.number_of_peers
        msg_length = struct.calcsize("!Ii")
        counter = 0

        # Peer self.id will forward by default all chunks received
        # from the splitter (originated at itself).
        self.forward[self.public_endpoint] = []

        while peers_pending_of_reception > 0:
            msg = self.splitter_socket.recv(msg_length)
            peer = struct.unpack("!Ii", msg)
            peer = (IP_tools.int2ip(peer[0]), peer[1])
            self.team.append(peer)
            if __debug__:
                if self.public_endpoint == peer:
                    self.lg.error(f"{self.ext_id}: I'm appending myself as a destination in my forwarding table")
                    
            # I'll forward at least the chunks received from the splitter.
            self.forward[self.public_endpoint].append(peer)
            self.pending[peer] = []
            
            self.say_hello(peer)
            #self.debts[peer] = 0
#            self.index_of_peer[peer] = counter
            #self.lg.info(f"{self.ext_id}: debs={self.debts}")
            #self.receive_the_list_of_peers__simulation(counter, peer)
            self.lg.info(f"{self.ext_id}: peer {peer} is in the team")
            counter += 1
            peers_pending_of_reception -= 1

        self.lg.info(f"{self.ext_id}: receive_the_list_of_peers: forward={self.forward} pending={self.pending}")

    def connect_to_the_splitter(self, peer_port):
        #print("{}: connecting to the splitter at {}".format(self.id,
        #                                                    self.splitter))
        self.lg.info(f"{self.public_endpoint}: connecting to the splitter at {self.splitter}")
        self.splitter_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.splitter_socket.set_id(self.id) # Ojo, simulation dependant
        #host = socket.gethostbyname(socket.gethostname())
        #iface = netifaces.interfaces()[1]      # Name of the second interface
        #stuff = netifaces.ifaddresses(iface)   # Configuration data
        #IP_stuff = stuff[netifaces.AF_INET][0] # Only the IP stuff
        #address = IP_stuff['addr']             # Get local IP addr
        host_name = socket.gethostname()
        address = socket.gethostbyname(host_name)
        self.splitter_socket.bind((address, peer_port))

        try:
            self.splitter_socket.connect(self.splitter)
        except ConnectionRefusedError as e:
            self.lg.error(f"{self.public_endpoint}: {e} when connecting to the splitter {self.splitter}")
            raise

        # The index for pending[].
        self.splitter = self.splitter_socket.getpeername() # Be careful, not "127.0.1.1 hostname" in /etc/hosts
        self.private_endpoint = self.splitter_socket.getsockname()
        #print("{}: I'm a peer".format(self.id))
        self.lg.info(f"{self.public_endpoint}: I am a peer")
        #self.neighbor = self.id
        #print("self.neighbor={}".format(self.neighbor))
        #self.pending[self.id] = []

        #print("{}: connected to the splitter at {}".format(self.id, self.splitter))
        self.lg.info(f"{self.public_endpoint}: connected to the splitter at {self.splitter}")

    # Why?
#    def send_ready_for_receiving_chunks(self):
#        # self.splitter_socket.send(b"R", "s") # R = Ready
#        msg = struct.pack("s", b"R")
#        self.splitter_socket.send(msg)
#        self.lg.info(f"{self.ext_id}: sent [ready] to {self.splitter}")

    def is_a_control_message(self, message):
        if message[0] < 0:
            return True
        else:
            return False

    def send_prune_origin(self, chunk_number, peer):
        msg = struct.pack("!ii", Messages.PRUNE, chunk_number)
        self.team_socket.sendto(msg, peer)
        self.lg.warning(f"{self.ext_id}: [prune {chunk_number}] sent to {peer}")

    def buffer_chunk(self, chunk_number, origin, chunk_data, sender):
        position = chunk_number % self.buffer_size
        if self.chunks[position][ChunkStructure.CHUNK_NUMBER] == chunk_number:
            self.lg.warning(f"{self.ext_id}: buffer_chunk: duplicate chunk {chunk_number} from {sender} (the first one was originated by {self.chunks[position][ChunkStructure.ORIGIN]})")
            if __debug__:
                i = 0
                for c in self.chunks:
                    self.lg.debug(f"{self.ext_id}: buffer_chunk: buffer[{i}]={c}")
                    i += 1
            self.send_prune_origin(chunk_number, sender)
        else:
            self.lg.info(f"{self.ext_id}: buffer_chunk: buffering ({chunk_number}, {chunk_data}, {origin}) sent by {sender} in position {position}")
            # New chunk. (chunk_number, chunk, origin) -> buffer[chunk_number]
            self.chunks[chunk_number % self.buffer_size] = (chunk_number, chunk_data, origin)

            #self.check__player_connected()
            if sender == self.splitter:

                #sys.stderr.write(f"{self.ext_id}: {self.pending}\n")
                
                # New round, all pending chunks are sent
                self.lg.info(f"{self.ext_id}: buffer_chunk: flushing chunks to {len(self.pending)} neighbors={self.pending.keys()}")
                for neighbor in self.pending:
                    self.lg.info(f"{self.ext_id}: buffer_chunk: flushing {len(self.pending[neighbor])} chunks to neighbor {neighbor}")
                    self.send_chunks(neighbor)

                # Delete the sent chunks of pending
                #for neighbor in self.pending:
                #    del self.pending[neighbor][:]  # Delete the content of the list, but no the pointer to the list
                        
                if __debug__:
                    self.rounds_counter += 1
                    for origin, neighbors in self.forward.items():
                        buf = ''
                        #for i in neighbors:
                        #    buf += str(i)
                        buf = len(neighbors)*"#"
                        self.lg.info(f"{self.ext_id}: round={self.rounds_counter:03} origin={origin} K={len(neighbors):02} fan-out={buf:10}")
                        self.lg.debug(f"{self.ext_id}: buffer_chunk: BUFFER={self.chunks}")
                    try:
                        CLR = self.number_of_lost_chunks / (chunk_number - self.prev_chunk_number_round)
                        self.lg.info(f"{self.ext_id}: CLR={CLR:1.3} losses={self.number_of_lost_chunks} chunk_number={chunk_number} increment={chunk_number - self.prev_chunk_number_round}")
                    except ZeroDivisionError:
                        pass
                    self.prev_chunk_number_round = chunk_number
                        
                self.number_of_lost_chunks = 0

                #sys.stderr.write(f"\nAntes: {self.ext_id}: {self.forward}")
                #sys.stderr.write(f"\n{self.ext_id}: {self.alive}")

                for origin in list(self.alive.keys()):
                    if self.alive[origin] == False:
                        del self.alive[origin]
                        for peers_list in self.forward.values():
                            if origin in peers_list:
                                peers_list.remove(origin)
                        if origin in self.team:
                            self.team.remove(origin)

                #sys.stderr.write(f"\nDespues: {self.ext_id}: {self.forward}")
                for origin in self.alive.keys():
                    self.alive[origin] = False
                
            else:

                self.alive[origin] = True
                # Chunk received from a peer
                
                #self.add_new_forwarding_rule(self.public_endpoint, sender)
                #self.lg.debug(f"{self.ext_id}: forward={self.forward}")

                if origin not in self.team:
                    if origin != self.public_endpoint:
                        # In the optimization stage, the peer
                        # could request to a neighbor a chunk that
                        # should be provided by the splitter (the
                        # peer is the origin). If this happens,
                        # the peer will receive chunks from
                        # neighbors for what he is the origin
                        # (that is not good, but neither a fatal
                        # error ... the peer will send a prunning
                        # message to the neighbor), but the peer
                        # should not be added to the team.
                        self.team.append(origin)
                        self.lg.info(f"{self.ext_id}: buffer_chunk: appended {origin} to team={self.team} by chunk from origin={origin}")

            if origin in self.forward:
                self.update_pendings(origin, chunk_number)

            if len(self.pending) > 0:
                neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
                self.lg.info(f"{self.ext_id}: buffer_chunk: selected neighbor={neighbor} neighbor_index={self.neighbor_index} len(pending)={len(list(self.pending.keys()))}")

                if __debug__:
                    c = 0
                    for n in self.pending:
                        self.lg.info(f"{self.ext_id}: buffer_chunk: {c} pending[{n}]={self.pending[n]}")
                        c += 1

                self.send_chunks(neighbor)

                # Select next entry in pending with chunks to send
                counter = 0
                while len(self.pending[neighbor]) == 0:
                    self.neighbor_index = list(self.pending.keys()).index(neighbor) + 1
                    neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
                    counter += 1
                    if counter > len(self.pending):
                        break

#                neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
#                self.lg.info(f"{self.ext_id}: buffer_chunk: selected neighbor={neighbor} neighbor_index={self.neighbor_index} len(pending)={len(list(self.pending.keys()))}")
#                self.send_chunks(neighbor)
#                self.neighbor_index = list(self.pending.keys()).index(neighbor) + 1

        self.lg.info(f"{self.ext_id}: buffer_chunk: buffer[{position}]={self.chunks[position]}")

    def update_pendings(self, origin, chunk_number):
        # A new chunk has been received, and this chunk has an origin
        # (not necessarily the sender of the chunk). For all peers P_i in
        # forward[origin] the chunk (number) is appended to pending[P_i].

        for peer in self.forward[origin]:
            try:
                self.pending[peer].append(chunk_number)
            except KeyError:
                self.pending[peer] = [chunk_number]

            self.lg.info(f"{self.ext_id}: update_pendings: appended {chunk_number} to pending[{peer}] which have a length of {len(self.pending[peer])}")
        self.lg.info(f"{self.ext_id}: update_pendings: len(pending)={len(self.pending)}")

#    def add_new_forwarding_rule(self, peer, neighbor):
#        try:
#            if neighbor not in self.forward[peer]:
#                self.lg.info(f"{self.ext_id}: {peer} added new neighbor {neighbor}")
##                if __debug__:
##                    if peer == neighbor:
##                        self.lg.error(f"{self.ext_id}: I'm appending myself to my forwarding table")
#                self.forward[peer].append(neighbor)
#                self.pending[neighbor] = []
#        except KeyError:
#            self.forward[peer] = [neighbor]
#            self.pending[neighbor] = []

    def compose_message(self, chunk_number):
        chunk_position = chunk_number % self.buffer_size
        chunk = self.chunks[chunk_position]
        stored_chunk_number = chunk[ChunkStructure.CHUNK_NUMBER]
        chunk_data = chunk[ChunkStructure.CHUNK_DATA]
        chunk_origin_IP = chunk[ChunkStructure.ORIGIN][0]
        chunk_origin_port = chunk[ChunkStructure.ORIGIN][1]
        content = (stored_chunk_number, chunk_data, IP_tools.ip2int(chunk_origin_IP), chunk_origin_port)
        self.lg.info(f"{self.ext_id}: compose_message: chunk_position={chunk_position} chunk_number={self.chunks[chunk_position][ChunkStructure.CHUNK_NUMBER]} origin={self.chunks[chunk_position][ChunkStructure.ORIGIN]}")
        packet = struct.pack(self.chunk_packet_format, *content)
        return packet

    def send_chunk_to_peer(self, chunk_number, destination):
        self.lg.info(f"{self.ext_id}: send_chunk_to_peer: chunk {chunk_number} sent to {destination}")
        msg = self.compose_message(chunk_number)
        #msg = struct.pack("isIi", stored_chunk_number, chunk_data, socket.ip2int(chunk_origin_IP), chunk_origin_port)
        self.team_socket.sendto(msg, destination)
        self.sendto_counter += 1
            #self.lg.debug("{}: sent chunk {} (with origin {}) to {}".format(self.ext_id, chunk_number, (chunk_origin_IP, chunk_origin_port), peer))
        #except TypeError:
        #    self.lg.warning(f"{self.ext_id}: chunk {chunk_number} not sent because it was lost")
        #    pass

    def process_request(self, chunk_number, sender):

        # If a peer X receives [request chunk] from peer Z, X will
        # append Z to forward[chunk.origin]. Only if Z is not the
        # origin of the requested chunk. This last thing can happen if
        # Z requests chunks that will be originated at itself.

        position = chunk_number % self.buffer_size
        if self.chunks[position][ChunkStructure.CHUNK_DATA] != b'L':
            origin = self.chunks[position][ChunkStructure.ORIGIN]
            if origin != sender:
                if origin in self.forward:
                    if sender not in self.forward[origin]:
                        self.forward[origin].append(sender)
                        self.pending[sender] = []
                else:
                    self.forward[origin] = [sender]
                    self.pending[sender] = []

        '''
        origin = self.chunks[chunk_number % self.buffer_size][ChunkStructure.ORIGIN]
        if origin != sender:
            self.lg.debug(f"{self.ext_id}: process_request: chunks={self.chunks}")

            self.lg.info(f"{self.ext_id}: process_request: received [request {chunk_number}] from {sender} (origin={origin})")

            # if origin[0] != None:
            if self.chunks[chunk_number % self.buffer_size][ChunkStructure.CHUNK_DATA] != b'L':
                # In this case, I can start forwarding chunks from origin.
                try:
                    self.lg.debug(f"{self.ext_id}: process_request: self.forward[{origin}]={self.forward[origin]} before")
                    if sender not in self.forward[origin]:
                        self.lg.debug(f"{self.ext_id}: process_request: adding {sender} to {self.forward[origin]}")
                        self.forward[origin].append(sender)
                        self.pending[sender] = []
                    else:
                        self.lg.debug(f"{self.ext_id}: process_request: {sender} is already in self.forward[{origin}]={self.forward[origin]}")
                except KeyError:
                    #self.forward[origin] = [sender] # OJOOOOOOOOOOOOOOOOOORRRRRRRRRRRRRRRRRRRRRRRRRRRRRR
                    self.pending[sender] = []
                #self.lg.debug(f"{self.ext_id}: process_request: self.forward[{origin}]={self.forward[origin]} after")
                self.lg.warning(f"{self.ext_id}: process_request: chunks from {origin} will be sent to {sender}")
                self.provide_request_feedback(sender)

                if __debug__:
                    if self.public_endpoint == origin:
                        self.lg.info(f"{self.ext_id}: process_request: sender={sender} added to the primary forwarding table (public_endpoint == origin={origin}) now with length {len(self.forward[self.public_endpoint])}")

            else:
                # I can't help :-(
                self.lg.warning(f"{self.ext_id}: process_request: request received from {sender}, but I have not the requested chunk {chunk_number} in my buffer")

            self.lg.debug(f"{self.ext_id}: process_request: length_forward={len(self.forward)} forward={self.forward}")

        else:
            self.lg.warning(f"{self.ext_id}: process_request: origin={origin} == sender={sender}. Request ignored")
        '''

    # When a {peer} receives a [prune {chunk_number}], the {sender} is
    # requesting that {peer} stop sending chunks originated at
    # {self.chunks[chunk_number % self.buffer_size].origin}.
    def process_prune(self, chunk_number, sender):

        def remove_sender(origin, sender):
            self.lg.debug(f"{self.ext_id}: process_prune: removing {sender} from forward[{origin}]={self.forward[origin]}")
            try:
                #sys.stderr.write(f"{self.ext_id}: process_prune: sender={sender} is going to be removed from forward[{origin}]={self.forward[origin]}\n")
                self.forward[origin].remove(sender)
                self.lg.warning(f"{self.ext_id}: process_prune: sender={sender} has been removed from forward[{origin}]={self.forward[origin]}")
                #sys.stderr.write(f"{self.ext_id}: process_prune: sender={sender} has been removed from forward[{origin}]={self.forward[origin]}\n")
            except ValueError:
                self.lg.error(f"{self.ext_id}: process_prune: failed to remove peer {sender} from forward={self.forward[origin]} for origin={origin} ")
            if len(self.forward[origin])==0:
                del self.forward[origin]
                if __debug__:
                    if origin in self.forward:
                        self.lg.info(f"{self.ext_id}: process_prune: origin {origin} is still in forward[{origin}]={self.forward[origin]}")
                    else:
                        self.lg.debug(f"{self.ext_id}: process_prune: origin={origin} removed from forward={self.forward}")
            if __debug__:
                if origin == self.public_endpoint:
                    try:
                        self.lg.info(f"{self.ext_id}: process_prune: sender={sender} removed from the primary forwarding table (public_endpoint == origin={origin}) now with length {len(self.forward[self.public_endpoint])}")
                    except KeyError:
                        pass
        
        position = chunk_number % self.buffer_size
        
        # Notice that chunk "chunk_number" should be stored in the
        # buffer because it has been sent to the neighbor that is
        # requesting the prune.
        
        if self.chunks[position][ChunkStructure.CHUNK_NUMBER] == chunk_number:
            origin = self.chunks[position][ChunkStructure.ORIGIN]
            self.lg.warning(f"{self.ext_id}: process_prune: [prune {chunk_number}] received from {sender} for pruning origin={origin}")
            #sys.stderr.write(f"{self.ext_id}: received [prune {chunk_number}] from {sender} for prunning {origin}")
            #if origin==self.public_endpoint:
            #    sys.stderr.write("!\n")
            #else:
            #    sys.stderr.write("\n")

            if origin in self.forward:
                self.lg.warning(f"{self.ext_id}: process_prune: origin={origin} is in forward")
                if sender in self.forward[origin]:
                    self.lg.debug(f"{self.ext_id}: process_prune: sender={sender} is in forward[{origin}]")
                    remove_sender(origin, sender)
                else:
                    self.lg.warning(f"{self.ext_id}: process_prune: sender={sender} is not in forward[{origin}]={self.forward[origin]}")
            else:
                self.lg.warning(f"{self.ext_id}: process_prune: origin={origin} is not in forward={self.forward}") 
        else:
            self.lg.warning(f"{self.ext_id}: process_prune: chunk_number={chunk_number} is not in buffer ({self.chunks[position][ChunkStructure.CHUNK_NUMBER]}!={chunk_number})")
            #sys.stderr.write(f"{self.ext_id}: chunk_number={chunk_number} is not in buffer ({self.chunks[position][ChunkStructure.CHUNK_NUMBER]}!={chunk_number})\n")

    def process_hello(self, sender):

        self.lg.debug("{}: received [hello] from {}".format(self.ext_id, sender))

        # Incoming peers request to the rest of peers of the team
        # those chunks whose source is the peer which receives the
        # request. So in the forwarding table of each peer will be an
        # entry indexed by <self.public_endpoint> (the origin peer
        # referenced by the incoming peer) what will point to the list
        # of peers of the team whose request has arrived (when
        # arriving). Other entries in the forwarding table will be
        # generated for other peers that request the explicit
        # forwarding of other chunks.

        # If a peer X receives [hello] from peer Z, X will
        # append Z to forward[X].

        if sender not in self.forward[self.public_endpoint]:
            self.forward[self.public_endpoint].append(sender)
            self.pending[sender] = []
            self.lg.info(f"{self.ext_id}: inserted {sender} in forward[{self.public_endpoint}] by [hello] from {sender} (forward={self.forward}) in round {self.rounds_counter}")
            #self.process_hello__simulation(sender)
            self.provide_hello_feedback(sender)

        if sender not in self.team:
            if __debug__:
                if sender == self.public_endpoint:
                    self.lg.error(f"{self.ext_id}: appending myself to the team by [hello]")
            self.team.append(sender)
            self.lg.info(f"{self.ext_id}: appended {sender} to team={self.team} by [hello]")
            #self.number_of_peers += 1
            
        #self.debts[sender] = 0s
        #self.lg.info(f"{self.ext_id}: inserted {sender} in {self.debts}")

    def process_goodbye(self, sender):
        self.lg.info(f"{self.ext_id}: process_goodbye: received [goodbye] from {sender}")

        if sender == self.splitter:
            self.lg.info(f"{self.ext_id}: process_goodbye: received [goodbye] from splitter")
            self.waiting_for_goodbye = False
            self.player_connected = False

        else:
            try:
                self.team.remove(sender)
                #self.number_of_peers -= 1
                self.lg.info(f"{self.ext_id}: process_goodbye: removed {sender} from team={self.team} by [goodbye]")
            except ValueError:
                self.lg.warning(f"{self.ext_id}: process_goodbye: failed to remove {sender} from team={self.team}")
#            try:
#                del self.index_of_peer[sender]
#            except KeyError:
#                self.lg.error(f"{self.ext_id}: failed to delete peer {sender} from index_of_peer={self.index_of_peer}")
            for peers_list in self.forward.values():
                self.lg.info(f"{self.ext_id}: process_goodbye: {sender} removing from {peers_list}")
                try:
                    peers_list.remove(sender)
                except ValueError:
                    self.lg.warning(f"{self.ext_id}: process_goodbye: failed to remove peer {sender} from {peers_list}")
            # sim.FEEDBACK["DRAW"].put(("O", "Node", "OUT", ','.join(map(str,sender))))     # To remove ghost peer

            
    # DBS peer's logic
    def process_unpacked_message(self, message, sender):

        chunk_number = message[ChunkStructure.CHUNK_NUMBER]
        self.lg.info(f"{self.ext_id}: process_unpacked_message: [{chunk_number}] <-- {sender}")
        #sys.stderr.write(str(message))

        if chunk_number >= 0:

            # We have received a chunk.
            chunk_data = message[ChunkStructure.CHUNK_DATA]
            origin = message[ChunkStructure.ORIGIN]
            chunk_data = message[ChunkStructure.CHUNK_DATA]

            self.lg.info(f"{self.ext_id}: process_unpacked_message: received chunk {chunk_number} from {sender} with origin {origin}")
            
            #sys.stdout.write(str(origin)); sys.stdout.flush()
            self.received_chunks += 1

#            if __debug__:
#                # Compute deltas
#                delta = chunk_number - self.prev_chunk_number
#                #self.chunk_number_delta = chunk_number - self.prev_received_chunk
#                self.lg.info(f"{self.ext_id}: process_unpacked_message: delta of chunk {chunk_number} is {delta}")
#                self.prev_chunk_number = chunk_number

            #self.process_unpacked_message__simulation_1(sender)
            self.provide_CLR_feedback(sender)

            self.buffer_chunk(chunk_number = chunk_number, origin = origin, chunk_data = chunk_data, sender = sender)

        else:  # message[ChunkStructure.CHUNK_NUMBER] < 0

            if chunk_number == Messages.REQUEST:
                self.process_request(message[1], sender)
            elif chunk_number == Messages.PRUNE:
                self.process_prune(message[1], sender)
            elif chunk_number == Messages.HELLO:
                # if len(self.forward[self.id]) < self.max_degree:
                self.process_hello(sender)
            elif chunk_number == Messages.GOODBYE:
                self.process_goodbye(sender)
            else:
                self.lg.info("{self.ext_id}: process_unpacked_message: unexpected control chunk of index={chunk_number}")

        return (chunk_number, sender)

    def send_chunks(self, neighbor):
        # When peer X receives a chunk, X selects the next
        # entry pending[E] (with one or more chunk numbers),
        # sends the chunk with chunk_number C indicated by
        # pending[E] to E, and removes C from pending[E]. If
        # in pending[E] there are more than one chunk
        # (number), all chunks are sent in a burst. E should
        # be selected to sent first to those peers that we
        # want to forward us chunks not originated in them.
        #   if self.neighbor in self.pending:
        self.lg.info(f"{self.ext_id}: send_chunks: (begin) neighbor={neighbor} pending[{neighbor}]={self.pending[neighbor]}")
        while self.pending[neighbor]:
            chunk_number = self.pending[neighbor].pop(0)
            self.lg.info(f"{self.ext_id}: send_chunks: sending chunk_number={chunk_number} to neighbor={neighbor}")
           
            if __debug__:
                if neighbor == self.public_endpoint:
                    self.lg.error(f"{self.ext_id}: send_chunks: sending a chunk {chunk_number} to myself={neighbor} forward={self.forward}")

            self.send_chunk_to_peer(chunk_number, neighbor)
            
#        for chunk_number in self.pending[neighbor]:
#            self.lg.info(f"{self.ext_id}: send_chunks: sending chunk_number={chunk_number} to neighbor={neighbor}")
            
#            if __debug__:
#                if neighbor == self.public_endpoint:
#                    self.lg.error(f"{self.ext_id}: send_chunks: sending a chunk {chunk_number} to myself={neighbor} forward={self.forward}")

#            self.send_chunk_to_peer(chunk_number, neighbor)
#        del self.pending[neighbor][:]  # Delete the content of the list, but no the pointer to the list:
        self.lg.info(f"{self.ext_id}: send_chunks: (end) neighbor={neighbor} pending[{neighbor}]={self.pending[neighbor]}")

    def receive_packet(self):
        #print("{}".format(self.max_packet_length))
        #sys.stderr.write(f"timeout={self.team_socket.gettimeout()}\n")
        '''
        try:
            return self.team_socket.recvfrom(self.max_packet_length)
        except self.team_socket.TimeoutException:
            sys.stderr.write('t'); sys.stderr.flush()
            self.timeouts += 1
            self.lg.warning(f"{self.ext_id}: timeouts={self.timeouts}")
        else:
            self.timeouts = 0
        '''
        #sys.stderr.write(f"{self.max_packet_length}\n")
        return self.team_socket.recvfrom(self.max_packet_length)

    def process_next_message(self):
        packet, sender = self.receive_packet()
        # self.lg.debug("{}: received {} from {} with length {}".format(self,id, pkg, sender, len(pkg)))
#        sys.stderr.write(f"packet={packet} from sender={sender}\n")
        return self.unpack_message(packet, sender)

    def unpack_message(self, packet, sender):
        if len(packet) == self.max_packet_length:
            message = struct.unpack(self.chunk_packet_format, packet)
            #sys.stderr.write("-->" + str(message) + "\n")
            message = message[ChunkStructure.CHUNK_NUMBER], \
                message[ChunkStructure.CHUNK_DATA], \
                (IP_tools.int2ip(message[ChunkStructure.ORIGIN]), message[ChunkStructure.ORIGIN+1])
            #sys.stderr.write("---->" + str(message) + "\n")
            
        elif len(packet) == struct.calcsize("!iii"):
            message = struct.unpack("!iii", packet)  # Control message: [control, parameter, parameter]
        elif len(packet) == struct.calcsize("!ii"):
            message = struct.unpack("!ii", packet)  # Control message: [control, parameter]
        else:
            message = struct.unpack("!i", packet)  # Control message: [control]
        x = self.process_unpacked_message(message, sender)
        return x

    # def process_message(self):
    #    return ((-1, b'L', None), ('127.0.1.1', 4552))

    def request_chunk(self, chunk_number, peer):
        msg = struct.pack("!ii", Messages.REQUEST, chunk_number)
        self.team_socket.sendto(msg, peer)
        self.lg.warning(f"{self.ext_id}: request_chunk: [request {chunk_number}] sent to {peer}")

    # Only monitors complain
    def complain(self, chunk_number):
        pass

    def play_chunk(self, chunk_number):
        buffer_box = self.chunks[chunk_number % self.buffer_size]
        if buffer_box[ChunkStructure.CHUNK_DATA] != b'L':
            # Only the data will be empty in order to remember things ...
            clear_entry_in_buffer = (buffer_box[ChunkStructure.CHUNK_NUMBER], b'L', buffer_box[ChunkStructure.ORIGIN])
#            self.chunks[chunk_number % self.buffer_size] = (-1, b'L', None)
            self.chunks[chunk_number % self.buffer_size] = clear_entry_in_buffer
            self.played += 1
        else:
            # The cell in the buffer is empty.
            self.complain(chunk_number) # Only monitors
            #self.complain(self.chunks[chunk_position][ChunkStructure.CHUNK_NUMBER]) # If I'm a monitor
            self.number_of_lost_chunks += 1
            self.lg.warning(f"{self.ext_id}: play_chunk: lost chunk! {self.chunk_to_play} (number_of_lost_chunks={self.number_of_lost_chunks})")

            # The chunk "chunk_number" has not been received on time
            # and it is quite probable that is not going to change
            # this in the near future. The action here is to request
            # the lost chunk to one or more peers using a [request
            # <chunk_number>]. If after this, I start receiving
            # duplicate chunks, then a [prune <chunk_number>] should
            # be sent to those peers which send duplicates.

            # Request the chunk to the origin peer of the last received chunk.
            #i = self.prev_received_chunk
            #destination = self.chunks[i % self.buffer_size][ChunkStructure.ORIGIN]
            # while destination == None:
            #    i += 1
            #    destination = self.chunks[i % self.buffer_size][ChunkStructure.ORIGIN]
            #self.request_chunk(chunk_number, destination)
            # And remove the peer in forward with higher debt.
            #print("{}: ------------> {}".format(self.ext_id, self.debt))
            # try:
            #    remove = max(self.debt, key=self.debt.get)
            # except ValueError:
            #    remove = self.neighbor
            # self.process_goodbye(remove)

            # We send the request to the neighbor that we have served.
            #self.request_chunk(chunk_number, self.neighbor)

            if len(self.team) > 1:
                self.request_chunk(chunk_number, random.choice(self.team))

            # Send the request to all neighbors.
            # for neighbor in self.forward[self.id]:
            #    self.request_chunk(chunk_number, neighbor)

            # Send the request to all the team.
            # for peer in self.team:
            #    self.request_chunk(chunk_number, peer)

            # As an alternative, to selected peer to send to it the
            # request, we run the buffer towards increasing positions
            # looking for a chunk whose origin peer is also a
            # neighbor. Doing that, we will found a neighbor that sent
            # its chunk to us a long time ago.

            # Here, self.neighbor has been selected by
            # simplicity. However, other alternatives such as
            # requesting the lost chunk to the neighbor with smaller
            # debt could also be explored.

            # try:
            #     self.request_chunk(chunk_number, min(self.debt, key=self.debt.get))
            # except ValueError:
            #     self.lg.debug("{}: debt={}".format(self.ext_id, self.debt))
            #     if self.neighbor is not None:  # Este if no debería existir
            #        self.request_chunk(chunk_number, self.neighbor)

        self.number_of_chunks_consumed += 1

        if __debug__:
            # Showing buffer
            buf = ""
            for i in self.chunks:
                if i[ChunkStructure.CHUNK_DATA] != b'L':
                    try:
                        _origin = self.team.index(i[ChunkStructure.ORIGIN])
                        buf += hash(_origin)
                    except ValueError:
                        buf += '-' # Peers do not exist in their team.
                        #peer_number = self.number_of_peers
                        #self.number_of_peers += 1
                    #buf += hash(peer_number)
                    #buf += '+'
                else:
                    buf += " "
            self.lg.debug(f"{self.ext_id}: play_chunk: buffer={buf}")

        #return self.player_connected

    def play_next_chunks(self, last_received_chunk):
        for i in range(last_received_chunk - self.prev_received_chunk):
            #self.player_connected = self.play_chunk(self.chunk_to_play)
            self.play_chunk(self.chunk_to_play)
            #self.chunks[self.chunk_to_play % self.buffer_size] = (-1, b'L', None)
            self.chunk_to_play = (self.chunk_to_play + 1) % Limits.MAX_CHUNK_NUMBER
        if ((self.prev_received_chunk % Limits.MAX_CHUNK_NUMBER) < last_received_chunk):
            self.prev_received_chunk = last_received_chunk

    def buffer_and_play(self):
        last_received_chunk = -1 # control message received
        while (last_received_chunk < 0) and self.player_connected:
            try:
                (last_received_chunk, _) = self.process_next_message()
            except TypeError:
                pass
            #except self.team_socket.TimeoutException:
    #    self.player_connected = False
            #    self.waiting_for_goodbye = False
            #    self.lg.error(f"{self.ext_id}: timeout!")
            #    break
#        (last_received_chunk, _) = self.process_next_message()
#        while last_received_chunk < 0:
#            if self.player_connected == False:
#                break
#            (last_received_chunk, _) = self.process_next_message()

        self.play_next_chunks(last_received_chunk)

    # To be placed in peer_dbs_sim ?
    def compose_goodbye_message(self):
        msg = struct.pack("!i", Messages.GOODBYE)
        return msg   

    # To be here (the above function if only for the simulator)
    # def compose_goodbye_message(self):
    #    msg = struct.pack("i", Messages.GOODBYE)
    #    return msg

    def say_goodbye(self, peer):
        # self.team_socket.sendto(Messages.GOODBYE, "i", peer)
        msg = self.compose_goodbye_message()
        self.team_socket.sendto(msg, peer)
        self.lg.info(f"{self.ext_id}: sent [goodbye] to {peer}")

    def say_goodbye_to_the_team(self):
        for origin, peer_list in self.forward.items():
            for peer in peer_list:
                self.say_goodbye(peer)

        # Next commented lines freeze the peer (in a receive() call)
        # while (all(len(d) > 0 for d in self.pending)):
        #     self.process_next_message()

        self.ready_to_leave_the_team = True
        self.lg.info(f"{self.ext_id}: sent [goodbye] to the team")

    def buffer_data(self):
        # Receive a chunk.
        (chunk_number, sender) = self.process_next_message()
        while (chunk_number < 0):
            (chunk_number, sender) = self.process_next_message()
            if self.player_connected == False:
                break
        # self.neighbor = sender

        # The first chunk to play is the firstly received chunk (which
        # probably will not be the received chunk with the smallest
        # index).
        self.chunk_to_play = chunk_number
#        sys.stderr.write(f"first_chunk_to_play={chunk_number}\n")

        self.lg.info(f"{self.ext_id}: buffer_data: position in the buffer of the first chunk to play={self.chunk_to_play}")

        while (chunk_number < self.chunk_to_play) or (((chunk_number - self.chunk_to_play) % self.buffer_size) < (self.buffer_size // 2)):
#            sys.stderr.write(f"{chunk_number} {self.chunk_to_play} "); sys.stderr.flush()
            (chunk_number, _) = self.process_next_message()
            if self.player_connected == False:
                break
            while (chunk_number < self.chunk_to_play):
                (chunk_number, _) = self.process_next_message()
                if self.player_connected == False:
                    break
        self.prev_received_chunk = chunk_number

    def run(self):
        self.lg.info(f"{self.ext_id}: waiting for stream chunks ...")

        for i in range(self.buffer_size):
            self.chunks.append((-1, b'L', None, 0))  # L == Lost

        start_time = time.time()
        self.buffer_data()
        buffering_time = time.time() - start_time
        self.lg.info(f"{self.ext_id}: buffering time={buffering_time}")
        #while (not self.is_the_player_disconected() or self.waiting_for_goodbye):
        while(self.player_connected and self.waiting_for_goodbye):
            self.buffer_and_play()
            # The goodbye messages sent to the splitter can be
            # lost. Therefore, it's a good idea to keep sending
            # [goodbye]'s to the splitter until the [goodbye] from the
            # splitter arrives.
            #if self.player_disconected() or self.received_goodbye():
            #    break
            self.lg.debug(f"{self.ext_id}: run: number_of_peers={len(self.team)}")
        self.lg.info(f"{self.ext_id}: run: player_connected={self.player_connected} waiting_for_goodbye={self.waiting_for_goodbye}")
        for i in range(10):
            self.say_goodbye(self.splitter)
            self.lg.info(f"{self.ext_id}: sent [goodbye] to the splitter {self.splitter}")
        self.say_goodbye_to_the_team()

        # Send pending chunks
        for peer, chunks in self.pending.items():
            for chunk in chunks:
                self.send_chunk_to_peer(chunk, peer)

        # Print some statistics
        total_lengths = 0
        #max_length = 0
        entries = 0
        for origin, peers_list in self.forward.items():
            self.lg.debug(f"{self.ext_id}: goodbye forward[{origin}]={peers_list} {len(peers_list)}")
            total_lengths += len(peers_list)
            if(len(peers_list) > 0):  # This should not be necessary
                entries += 1
            # if max_length < len(peers_list):
            #    max_length = len(peers_list)
        #print("{}: forward={} forward_entries={} max_length={}".format(self.ext_id, self.forward, entries, max_length))
        try:
            avg = total_lengths/entries
        except:
            avg = 0
        self.lg.info(f"{self.ext_id}: average_neighborhood_degree={avg} ({total_lengths}/{entries})") # Wrong!!!!!!!!!!!!!!!!!!!!!

        self.lg.debug(f"{self.ext_id}: forward = {self.forward}")

#                print("------------------------------------", peer, "/", chunk)
#        for peer in self.forward:
#            print("=================================", self.pending)
#            if peer in self.pending:
#                print(peer, "in", self.pending)
#                for chunk in self.pending[peer][:]:
#                    print("sent chunk", chunk, "to", peer)
#                    self.send_chunk(chunk, peer)

        self.team_socket.close()

    def start(self):
        Thread(target=self.run).start()

    # Unused
    def am_i_a_monitor(self):
        return self.number_of_peers < self.number_of_monitors

    # def set_id(self):
    #     # At this moment, I don't know any other peer.
    #     self.id = self.splitter_socket.getsockname()
    #     self.forward[self.id] = []
# Old stuff:

# During their life in the team (for example, when a peer refuse to
# send data to it o simply to find better routes), peers will request
# alternative routes for the chunks. To do that, a [send once from
# <origin peer>] message will be sent to at least one peer of the
# team. A peer that receive such message will send (or not, depending
# on, for example, the debt of the requesting peer) only one chunk
# from the origin peer to the requesting peer. The requesting peer
# will send to the first peer to send the chunk a [send from <origin
# peer>] and both peers will be neighbors. To cancel this message, a
# [prune <origin>] must be used.
