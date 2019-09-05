"""
@package simulator
peer_dbs module
"""

# Just copied from peer_dbs. Remove the unnecessary.

# Abstract class

# DBS (Data Broadcasting Set) layer, peer side.

# DBS peers receive chunks from the splitter and other peers, and
# resend them, depending on the forwarding requests performed by the
# peers. In a nutshell, if a peer X wants to receive from peer Y
# the chunks from origin Z, X must request it to Y, explicitally.

import sys
import time
import struct
import logging
#from colorlog import ColorLog
#import netifaces
from threading import Thread
#from .common import Common
from .chunk_structure import ChunkStructure
from .messages import Message
from .limits import Limits
#from .simulator_stuff import Simulator_socket as socket
from .socket_wrapper import Socket_wrapper as socket
from .ip_tools import IP_tools
from .simulator_stuff import hash
import random

class Peer_DBS():

    peer_port = 4553
    splitter = ("localhost", 4552)

    def __init__(self,
                 id,
                 name,
                 max_chunk_loss,
                 loglevel):

        #logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(levelname)s %(name)s %(message)s")
        #self.lg = ColorLog(logging.getLogger(name))
        self.lg = logging.getLogger(name)
        self.lg.setLevel(loglevel)

        # Peer identification. Depending on the simulation accuracy, it
        # can be a simple string or an (local) endpoint.
        self.id = None

        # S I M U L A T I O N
        self._id = id

        # Maximum number of lost chunks before removing a peer in the team.
        self.max_chunk_loss = max_chunk_loss
        
        # Chunk currently played.
        #self.chunk_to_play = 0

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

        # Number of peers in the team (except for knowing if I'm a
        # monitor, unused).
        #self.number_of_peers = 0

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
        # those peers that has sent to this peer a chunk in the last
        # max_chunk_loss rounds.
        self.team = []

        # Supportiviy of each peer of the known team. For a given
        # peer, stores a counter that in incremented each time a chunk
        # is received from that peer and decremented each time a chunk
        # is received from the splitter. The number of peers in
        # supportivity.keys() is the fan-in of the peer.
        self.supportivity = {}

        # Sent and received chunks.
        self.sendto_counter = 0

        # S I M U L A T I O N
        self.received_chunks = 0

        # The longest message expected to be received: chunk_number
        # (i=int32), IP address of the origin peer (I=unsigned int32)
        # and port of the origin peer (i), a timestamp (d=double), and
        # the chunk data (s=string), that in the simulator has ONLY
        # one character. !!!!!!!!!!!!!!Esta cadena debería calcularse cuando se conociera la longitud del chunk, que debería enviarse siempre, incluso en el simulador !!!!!!!!!!!!!!!!! 
        self.chunk_packet_format = "!iIids"
        self.max_packet_length = struct.calcsize(self.chunk_packet_format)
        self.lg.info(f"{self.id}: max_packet_length={self.max_packet_length}")

        self.neighbor_index = 0

        # Played or lost
        self.number_of_chunks_consumed = 0

        # S I M U L A T I O N
        self.number_of_lost_chunks = 0

        # S I M U L A T I O N
        self.played = 0

        # S I M U L A T I O N
        #self.link_failure_prob = 0.0

        self.rounds_counter = 0

        if __debug__:
            self.prev_chunk_number = 0  # Jitter in chunks-time

        #self.debts = {}
        #self.max_debt = 8
        self.name = name
        self.lg.info(f"{name} {self.id}: DBS initialized")

    def set_splitter(self, splitter):
        self.splitter = splitter

    def set_max_degree(self, max_degree):
        self.max_degree = max_degree
        
    def listen_to_the_team(self):
        self.team_socket = socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, loglevel=self.lg.level)
        self.team_socket.bind(self.id)
        self.lg.info(f"{self.ext_id}: listening to the team")
        self.say_hello(self.splitter) # Only works for cone NATs
        #self.team_socket.bind(("", self.id[1]))
        #self.team_socket.settimeout(self.timeout) # In seconds
        #self.team_socket.setblocking(0)

    def receive_public_endpoint(self):
        msg_length = struct.calcsize("!Ii")
        msg = self.splitter_socket.recv(msg_length)
        pe = struct.unpack("!Ii", msg)
        self.public_endpoint = (IP_tools.int2ip(pe[0]), pe[1])
        self.lg.info(f"{self.id}: public_endpoint={self.public_endpoint}")

        #self.peer_number = self.number_of_peers
        self.ext_id = ("%03d" % self.peer_index_in_team, self.public_endpoint[0], "%5d" % self.public_endpoint[1])
        self.lg.info(f"{self.ext_id}: peer_index_in_team={self.peer_index_in_team}")
        sys.stderr.write(f"{self.name} {self.ext_id} alive :-)\n")
        #sys.stderr.flush()

    def receive_buffer_size(self):
        # self.buffer_size = self.splitter_socket.recv("H")
        # self.buffer_size = self.recv("H")
        msg_length = struct.calcsize("!H")
        msg = self.splitter_socket.recv(msg_length)
        self.buffer_size = struct.unpack("!H", msg)[0]
        self.lg.info(f"{self.ext_id}: buffer_size={self.buffer_size}")

    def receive_the_number_of_peers(self):
#        msg_length = struct.calcsize("!H")
#        msg = self.splitter_socket.recv(msg_length)
#        self.number_of_monitors = struct.unpack("!H", msg)[0]
#        self.lg.info(f"{self.id}: number_of_monitors={self.number_of_monitors}")

        msg_length = struct.calcsize("!H")
        msg = self.splitter_socket.recv(msg_length)
        self.number_of_peers = struct.unpack("!H", msg)[0]
        self.lg.info(f"{self.ext_id}: number_of_peers = {self.number_of_peers}")

    def receive_peer_index_in_team(self):
        msg_length = struct.calcsize("!H")
        msg = self.splitter_socket.recv(msg_length)
        self.peer_index_in_team = struct.unpack("!H", msg)[0]
        self.lg.info(f"{self.id}: peer_index_in_team = {self.peer_index_in_team}")

    def say_hello(self, entity):
        msg = struct.pack("!i", Message.HELLO)
        self.team_socket.sendto(msg, entity)
        self.lg.info(f"{self.ext_id}: sent [hello] to {entity}")

    #def receive_the_list_of_peers__simulation(self, counter, peer):
    #    pass
    
    def receive_the_list_of_peers(self):
#        self.index_of_peer = {}
        peers_pending_of_reception = self.number_of_peers
        msg_length = struct.calcsize("!Ii")
        counter = 0

        # Peer self.id will forward by default all chunks originated
        # at itself.
        self.forward[self.public_endpoint] = []

        while peers_pending_of_reception > 0:
            msg = self.splitter_socket.recv(msg_length)
            peer = struct.unpack("!Ii", msg)
            peer = (IP_tools.int2ip(peer[0]),peer[1])
            self.team.append(peer)
            #if counter < self.max_degree:
            self.forward[self.public_endpoint].append(peer)
            self.say_hello(peer)
            #self.debts[peer] = 0
            self.supportivity[peer] = 0
#            self.index_of_peer[peer] = counter
            #self.lg.info(f"{self.ext_id}: debs={self.debts}")
            #self.receive_the_list_of_peers__simulation(counter, peer)
            self.lg.info(f"{self.ext_id}: peer {peer} is in the team")
            counter += 1
            peers_pending_of_reception -= 1

        self.lg.info(f"{self.ext_id}: forward={self.forward} pending={self.pending}")

    def connect_to_the_splitter(self, peer_port):
        #print("{}: connecting to the splitter at {}".format(self.id,
        #                                                    self.splitter))
        self.lg.info(f"{self.id}: connecting to the splitter at {self.splitter}")
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
            self.lg.error(f"{self.id}: {e} when connecting to {self.splitter}")
            raise

        # The index for pending[].
        self.splitter = self.splitter_socket.getpeername() # Be careful, not "127.0.1.1 hostname" in /etc/hosts
        self.id = self.splitter_socket.getsockname()
        #print("{}: I'm a peer".format(self.id))
        self.lg.info(f"{self.id}: I am a peer")
        #self.neighbor = self.id
        #print("self.neighbor={}".format(self.neighbor))
        #self.pending[self.id] = []

        #print("{}: connected to the splitter at {}".format(self.id, self.splitter))
        self.lg.info(f"{self.id}: connected to the splitter at {self.splitter}")

    # Why?
    def send_ready_for_receiving_chunks(self):
        # self.splitter_socket.send(b"R", "s") # R = Ready
        msg = struct.pack("s", b"R")
        self.splitter_socket.send(msg)
        self.lg.info(f"{self.ext_id}: sent [ready] to {self.splitter}")

    def is_a_control_message(self, message):
        if message[0] < 0:
            return True
        else:
            return False

    def prune_origin(self, chunk_number, peer):
        msg = struct.pack("!ii", Message.PRUNE, chunk_number)
        self.team_socket.sendto(msg, peer)
        self.lg.warning(f"{self.ext_id}: [prune {chunk_number}] sent to {peer}")

    def buffer_new_chunk(self, chunk_number, origin, timestamp, chunk_data, sender):
        self.lg.info(f"{self.ext_id}: received chunk {(chunk_number, chunk_data, origin)} from {sender}")
        # New chunk. (chunk_number, chunk, origin) -> buffer[chunk_number]
        self.chunks[chunk_number % self.buffer_size] = (chunk_number, origin, timestamp, chunk_data)

    def update_pendings(self, origin, chunk_number):
        # A new chunk has been received, and this chunk has an origin
        # (not necessarily the sender of the chunk). For all peers P_i in
        # forward[origin] the chunk (number) is appended to pending[P_i].
        
        #print("{}: update_pendings({}, {})".format(self.ext_id, origin, chunk_number))
        for peer in self.forward[origin]:
                #if sefl.pending[peer] = None:
                #    self.peer_number[peer] = []
            try:
                self.pending[peer].append(chunk_number)
            except KeyError:
                self.pending[peer] = [chunk_number]

                #self.lg.error("{}: KeyError update_pendings(origin={}, chunk_number={}) forward={} pending={}".format(self.ext_id, origin, chunk_number, self.forward, self.pending))
                #raise
            self.lg.info(f"{self.ext_id}: appended {chunk_number} to pending[{peer}]")
        self.lg.info(f"{self.ext_id}: pending={self.pending}")
        #self.lg.debug("{}: forward[{}]={}".format(self.ext_id, origin, self.forward[origin]))

    def add_new_forwarding_rule(self, peer, neighbor):
        try:
            if neighbor not in self.forward[peer]:
                self.lg.info(f"{self.ext_id}: {peer} added new neighbor {neighbor}")
                self.forward[peer].append(neighbor)
                self.pending[neighbor] = []
                self.supportivity[neighbor] = 0
        except KeyError:
            self.forward[peer] = [neighbor]
            self.pending[neighbor] = []
            self.supportivity[neighbor] = 0

    def compose_message(self, chunk_number):
        chunk_position = chunk_number % self.buffer_size
        chunk = self.chunks[chunk_position]
        stored_chunk_number = chunk[ChunkStructure.CHUNK_NUMBER]
        chunk_origin = chunk[ChunkStructure.ORIGIN]
        #chunk_origin_IP = chunk[ChunkStructure.ORIGIN_IP]
        #chunk_origin_port = chunk[ChunkStructure.ORIGIN_PORT]
        timestamp = chunk[ChunkStructure.TIMESTAMP]
        chunk_data = chunk[ChunkStructure.CHUNK_DATA]
        #sys.stderr.write(f"---> {stored_chunk_number} {chunk_origin} {timestamp}\n")
        content = (stored_chunk_number,
                   IP_tools.ip2int(chunk_origin[0]), chunk_origin[1],
                   timestamp,
                   chunk_data)
        packet = struct.pack(self.chunk_packet_format, *content)
        return packet
    
    def send_chunk_to_peer(self, chunk_number, destination):
        self.lg.info(f"{self.ext_id}: [{chunk_number}] --> {destination}")
        msg = self.compose_message(chunk_number)
        #msg = struct.pack("isIi", stored_chunk_number, chunk_data, socket.ip2int(chunk_origin_IP), chunk_origin_port)
        self.team_socket.sendto(msg, destination)
        self.sendto_counter += 1
            #self.lg.debug("{}: sent chunk {} (with origin {}) to {}".format(self.ext_id, chunk_number, (chunk_origin_IP, chunk_origin_port), peer))
        #except TypeError:
        #    self.lg.warning(f"{self.ext_id}: chunk {chunk_number} not sent because it was lost")
        #    pass

#    def process_request(self, sender):
#        pass
        
    def process_request(self, chunk_number, sender):

        # If a peer X receives [request Y] from peer Z, X will
        # append Z to forward[Y.origin].

        origin = self.chunks[chunk_number % self.buffer_size][ChunkStructure.ORIGIN]

        self.lg.debug(f"{self.ext_id}: received [request {chunk_number}] from {sender} (origin={origin}, forward={self.forward})")

        if origin[0] != None:
            # In this case, I can start forwarding chunks from origin.
            # Ojo, funciona con:
            #self.forward[origin] = [sender]
            # pero yo creo que debiera ser:
            if origin in self.forward:
                if len(self.forward[origin]) == 0:
                    self.forward[origin] = [sender]
                    self.pending[sender] = []
                else:
                    if sender not in self.forward[origin]:
                        self.forward[origin].append(sender)
                        self.pending[sender] = []
            else:
                self.forward[origin] = []
                self.pending[sender] = []
            self.lg.info(f"{self.ext_id}: chunks from {origin} will be sent to {sender}")
            self.provide_request_feedback(sender)
        else:
            # Otherwise, I can't help.
            self.lg.info(f"{self.ext_id}: request received from {sender}, but I have not the requested chunk {chunk_number} in my buffer={self.chunks}")

        self.lg.debug(f"{self.ext_id}: chunk={self.chunks[chunk_number % self.buffer_size]} origin={origin} forward={self.forward}")
        self.lg.debug(f"{self.ext_id}: length_forward={len(self.forward)} forward={self.forward}")

    def process_prune(self, chunk_number, sender):
        self.lg.warning(f"{self.ext_id}: [prune {chunk_number}] received from {sender}".format(self.ext_id, chunk_number, sender))
        chunk = self.chunks[chunk_number % self.buffer_size]
        # Notice that chunk_number must be stored in the buffer
        # because it has been sent to a neighbor.
        origin = chunk[ChunkStructure.ORIGIN]
        if origin in self.forward:
            if sender in self.forward[origin]:
                try:
                    self.forward[origin].remove(sender)
                    self.lg.info(f"{self.ext_id}: [prune {chunk_number}] <- {sender}, which is removed from forward[origin={origin}]={self.forward[origin]}")
                except ValueError:
                    self.lg.error(f"{self.public_endpoint}: failed to remove peer {sender} from forward table {self.forward[origin]} for origin {origin} ")
                if len(self.forward[origin])==0:
                    del self.forward[origin]

#    def process_hello__simulation(self, sender):
#        pass

    def process_hello(self, sender):
        self.lg.debug("{}: received [hello] from {}".format(self.ext_id, sender))

        # Incoming peers request to the rest of peers of the
        # team those chunks whose source is the peer which
        # receives the request. So in the forwarding table of
        # each peer will be an entry indexed by <self.id> (the
        # origin peer referenced by the incoming peer) what
        # will point to the list of peers of the team whose
        # request has arrived (when arriving). Other entries
        # in the forwarding table will be generated for other
        # peers that request the explicit forwarding of other
        # chunks.

        # If a peer X receives [hello] from peer Z, X will
        # append Z to forward[X].

        if sender not in self.forward[self.public_endpoint]:
            self.forward[self.public_endpoint].append(sender)
            self.pending[sender] = []
            self.lg.info(f"{self.ext_id}: inserted {sender} in forward[{self.public_endpoint}] by [hello] from {sender} (forward={self.forward}) in round {self.rounds_counter}")
            #self.process_hello__simulation(sender)
            self.provide_hello_feedback(sender)

        if sender not in self.team:
            self.team.append(sender)
            self.lg.info(f"{self.ext_id}: appended {sender} to team")
            self.number_of_peers += 1
            self.supportivity[sender] = 0
            
        #self.debts[sender] = 0s
        #self.lg.info(f"{self.ext_id}: inserted {sender} in {self.debts}")

    def process_goodbye(self, sender):
        self.lg.info(f"{self.ext_id}: received [goodbye] from {sender}")

        if sender == self.splitter:
            self.lg.info(f"{self.ext_id}: received [goodbye] from splitter")
            self.waiting_for_goodbye = False
            self.player_connected = False

        else:
            try:
                self.team.remove(sender)
                self.number_of_peers -= 1
                self.lg.info(f"{self.ext_id}: removed peer {sender} from team={self.team}")
            except ValueError:
                self.lg.warning(f"{self.ext_id}: failed to remove peer {sender} from team={self.team}")
#            try:
#                del self.index_of_peer[sender]
#            except KeyError:
#                self.lg.error(f"{self.ext_id}: failed to delete peer {sender} from index_of_peer={self.index_of_peer}")
            for peers_list in self.forward.values():
                if sender in peers_list:
                    self.lg.info(f"{self.ext_id}: {sender} removing from {peers_list}")
                    try:
                        peers_list.remove(sender)
                    except ValueError:
                        self.lg.warning(f"{self.ext_id}: failed to remove peer {sender} from {peers_list}")
            # sim.FEEDBACK["DRAW"].put(("O", "Node", "OUT", ','.join(map(str,sender))))     # To remove ghost peer

            del self.supportivity[sender]
            
    # DBS peer's logic
    def process_unpacked_message(self, message, sender):
        chunk_number = message[ChunkStructure.CHUNK_NUMBER]
        self.lg.info(f"{self.ext_id}: [{chunk_number}] <-- {sender}")
        #sys.stderr.write(str(message))

        if chunk_number >= 0:
            # We have received a chunk.
            origin = message[ChunkStructure.ORIGIN]
            timestamp = message[ChunkStructure.TIMESTAMP]
            chunk_data = message[ChunkStructure.CHUNK_DATA]
            now = time.time()
            latency = now - timestamp
            self.lg.info(f"{self.ext_id}: latency = {latency}")
            #sys.stdout.write(str(origin)); sys.stdout.flush()
            self.received_chunks += 1

            if __debug__:
                # Compute deltas
                delta = chunk_number - self.prev_chunk_number
                #self.chunk_number_delta = chunk_number - self.prev_received_chunk
                self.lg.info(f"{self.ext_id}: delta of chunk {chunk_number} is {delta}")
                self.prev_chunk_number = chunk_number

            #self.process_unpacked_message__simulation_1(sender)
            self.provide_CLR_feedback(sender)

            # 1. Store chunk or report duplicate
            if self.chunks[chunk_number % self.buffer_size][ChunkStructure.CHUNK_NUMBER] == chunk_number:
                # Duplicate chunk. Ignore it and warn the sender to
                # stop sending more chunks from the origin of the received
                # chunk "chunk_number".
                self.lg.warning(f"{self.ext_id}: duplicate chunk {chunk_number} from {sender} (the first one was sent by {self.chunks[chunk_number % self.buffer_size][ChunkStructure.ORIGIN]})")
                #if __debug__:
                #    self.lg.debug(f"BUFFER={self.chunks}")
                self.prune_origin(chunk_number, sender)
            else:
                self.buffer_new_chunk(chunk_number = chunk_number,
                                      origin = origin,
                                      timestamp = timestamp,
                                      chunk_data = chunk_data,
                                      sender = sender)

                if __debug__:
                    # Showing buffer
                    buf = ""
                    for i in self.chunks:
                        if i[ChunkStructure.CHUNK_NUMBER] > -1:
                            try:
                                _origin = self.team.index(i[ChunkStructure.ORIGIN])
                                buf += hash(_origin)
                            except ValueError:
                                buf += '-'
                                #peer_number = self.number_of_peers
                                #self.number_of_peers += 1
                            #buf += hash(peer_number)
                            #buf += '+'
                        else:
                            buf += " "
                    self.lg.debug(f"{self.ext_id}: buffer={buf}")

                #self.check__player_connected()
                if sender == self.splitter:
                    # Received a chunk from the splitter.
                    
                    #for peer, debt in self.debts:
                    #    debt //= 2
                    self.lg.info(f"{self.ext_id}: supportivity = {self.supportivity}")
                    
                    self.rounds_counter += 1
                    for peer in self.supportivity:
                        self.supportivity[peer] -= 1
                        self.lg.info(f"{self.ext_id}: self.supportivity[{peer}] = {self.supportivity[peer]}")
                        if self.supportivity[peer] <= -self.max_chunk_loss:
                            self.lg.warning(f"{self.ext_id}: peer {sender} removed of the team by selfish")
                            try:
                                self.team.remove(peer)
                            except ValueError:
                                self.lg.error(f"{self.ext_id}: team={self.team} peer={peer}")
#                            try:
#                                del self.index_of_peer[peer]
#                            except KeyError:
#                                self.lg.error(f"{self.ext_id}: index_of_peer={self.index_of_peer} peer={peer}")
                                
                            self.number_of_peers -= 1
                            self.forward[origin].remove(peer)
                            if len(self.forward[origin]) == 0:
                                del self.forward[origin]
                            for chunk in self.pending[peer]:
                                self.pending[peer].remove(chunk)
                            if len(self.pending[peer]) == 0:
                                del self.pending[peer]
                                
#                        except KeyError:
#                            pass
#                        except ValueError:
#                            pass
                    
                    if __debug__:
                        neighbors = list(self.pending.keys())
                        for peer in neighbors:
                            if len(neighbors) > 0:
                                buf = len(neighbors)*"#"
                                self.lg.debug(f"{self.ext_id}: fan-out({peer})) {buf} {len(neighbors)}")
                        self.lg.debug(f"{self.ext_id}: team={self.team}")

                    
                else:
                    # Received a chunk from a peer.
                    #try:
                    #    self.debts[sender] -= 1
                    #except KeyError:
                    #    pass
                    self.lg.info(f"splitter={self.splitter}")
                    self.add_new_forwarding_rule(self.public_endpoint, sender)
                    self.lg.debug(f"{self.ext_id}: forward={self.forward}")

                    try:
                        self.supportivity[sender] += 1
                    except KeyError:
                        # New sender
                        self.supportivity[sender] = 0
                    
                if origin in self.forward:
                    self.update_pendings(origin, chunk_number)

                if len(self.pending) > 0:
                    neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
                    #neighbor = sorted(zip(list(self.pending.keys()), list(self.supportivity.values())))[(self.neighbor_index) % len(self.pending)][0]
                    self.send_chunks(neighbor)
                    self.neighbor_index = list(self.pending.keys()).index(neighbor) + 1

        else:  # message[ChunkStructure.CHUNK_NUMBER] < 0

            if chunk_number == Message.REQUEST:
                self.process_request(message[1], sender)
            elif chunk_number == Message.PRUNE:
                self.process_prune(message[1], sender)
            elif chunk_number == Message.HELLO:
                #if len(self.forward[self.id]) < self.max_degree:
                self.process_hello(sender)
            elif chunk_number == Message.GOODBYE:
                self.process_goodbye(sender)
            else:
                self.lg.info("{self.ext_id}: unexpected control chunk of index={chunk_number}")

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
        self.lg.info(f"{self.ext_id}: send_chunks (begin) neighbor={neighbor} pending[{neighbor}]={self.pending[neighbor]}")
        for chunk_number in self.pending[neighbor]:
            self.lg.info(f"{self.ext_id}: send_chunks sel_chunk={chunk_number} to neighbor={neighbor}")
            self.send_chunk_to_peer(chunk_number, neighbor)
        self.pending[neighbor] = []
        #for chunk_number in self.pending[self.neighbor]:
        #    self.pending[self.neighbor].remove(chunk_number)
        self.lg.info(f"{self.ext_id}: send_chunks (end) neighbor={neighbor} pending[{neighbor}]={self.pending[neighbor]}")

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
        pkg, sender = self.receive_packet()
        # self.lg.debug("{}: received {} from {} with length {}".format(self,id, pkg, sender, len(pkg)))
        return self.unpack_message(pkg, sender)

    def unpack_message(self, packet, sender):
        if len(packet) == self.max_packet_length:
            message = struct.unpack(self.chunk_packet_format, packet)
            #sys.stderr.write("-->" + str(message) + "\n")
            message = (message[ChunkStructure.CHUNK_NUMBER],
                       (IP_tools.int2ip(message[ChunkStructure.ORIGIN]),
                       message[ChunkStructure.ORIGIN+1]),
                       message[ChunkStructure.TIMESTAMP+1],
                       message[ChunkStructure.CHUNK_DATA+1])
            #sys.stderr.write("---->" + str(message) + "\n")
            
        elif len(packet) == struct.calcsize("!iii"):
            message = struct.unpack("!iii", packet)  # Control message: [control, parameter, parameter]
        elif len(packet) == struct.calcsize("!ii"):
            message = struct.unpack("!ii", packet)  # Control message: [control, parameter]
        else:
            message = struct.unpack("!i", packet)  # Control message: [control]
        x = self.process_unpacked_message(message, sender)
        return x

    #def process_message(self):
    #    return ((-1, b'L', None), ('127.0.1.1', 4552))

    def request_chunk(self, chunk_number, peer):
        msg = struct.pack("!ii", Message.REQUEST, chunk_number)
        self.team_socket.sendto(msg, peer)
        self.lg.warning(f"{self.ext_id}: [request {chunk_number}] sent to {peer}")

    # Only monitors complain
    def complain(self, chunk_number):
        pass

    def play_chunk(self, chunk_number):
        buffer_box = self.chunks[chunk_number % self.buffer_size]
        if buffer_box[ChunkStructure.CHUNK_NUMBER] > -1:
            # Played chunks are labeled with chunk_number=-1.
            #self.chunks[chunk_number % self.buffer_size] = (-1, b'L', None)
            chunk_entry_in_buffer = (-1,
                                     self.chunks[chunk_number % self.buffer_size][ChunkStructure.ORIGIN],
                                     0.0,
                                     b'L')
            self.chunks[chunk_number % self.buffer_size] = chunk_entry_in_buffer
            self.played += 1
        else:
            self.complain(chunk_number)
            self.number_of_lost_chunks += 1
            self.lg.warning(f"{self.ext_id}: lost chunk! {chunk_number} (number_of_lost_chunks={self.number_of_lost_chunks})")

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
            #while destination == None:
            #    i += 1
            #    destination = self.chunks[i % self.buffer_size][ChunkStructure.ORIGIN]
            #self.request_chunk(chunk_number, destination)
            # And remove the peer in forward with higher debt.
            #print("{}: ------------> {}".format(self.ext_id, self.debt))
            #try:
            #    remove = max(self.debt, key=self.debt.get)
            #except ValueError:
            #    remove = self.neighbor
            #self.process_goodbye(remove)
            
            # We send the request to the neighbor that we have served.
            #self.request_chunk(chunk_number, self.neighbor)

            if len(self.team) > 0:
                # Request the lost chunk to a random peer of the known team.
                self.request_chunk(chunk_number, random.choice(self.team))
                # Request the chunk to the peer with the minimun number of lost chunks.
                #try:
                #    self.request_chunk(chunk_number, max(self.supportivity, key = self.supportivity.get))
                #except ValueError:
                #    pass

            # Send the request to all neighbors.
            #for neighbor in self.forward[self.id]:
            #    self.request_chunk(chunk_number, neighbor)

            # Send the request to all the team.
            #for peer in self.team:
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
        #return self.player_connected

    def play_next_chunks(self, last_received_chunk):
        for i in range(last_received_chunk - self.prev_received_chunk):
            #self.player_connected = self.play_chunk(self.chunk_to_play)
            self.play_chunk(self.chunk_to_play)
            #self.chunks[self.chunk_to_play % self.buffer_size] = (-1, b'L', None)
            self.chunk_to_play = (self.chunk_to_play + 1) % Limits.MAX_CHUNK_NUMBER
        if ((self.prev_received_chunk % Limits.MAX_CHUNK_NUMBER) < last_received_chunk):
            self.prev_received_chunk = last_received_chunk
        self.lg.info(f"{self.ext_id}: run = {self.prev_received_chunk - last_received_chunk}")

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

    def compose_goodbye_message(self):
        msg = struct.pack("!i", Message.GOODBYE)
        return msg   

    # To be here (the above function if only for the simulator)
    # def compose_goodbye_message(self):
    #    msg = struct.pack("i", Message.GOODBYE)
    #    return msg

    def say_goodbye(self, peer):
        # self.team_socket.sendto(Message.GOODBYE, "i", peer)
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

        self.lg.info(f"{self.ext_id}: position in the buffer of the first chunk to play={self.chunk_to_play}")

        while (chunk_number < self.chunk_to_play) or (((chunk_number - self.chunk_to_play) % self.buffer_size) < (self.buffer_size // 2)):
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
            self.chunks.append((-1, (None, 0), 0.0, b'L'))  # L == Lost

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
            if __debug__:
                self.lg.debug(f"{self.ext_id}: number_of_peers={self.number_of_peers}")
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
            if(len(peers_list)>0): # This should not be necessary
                entries += 1
            #if max_length < len(peers_list):
            #    max_length = len(peers_list)
        #print("{}: forward={} forward_entries={} max_length={}".format(self.ext_id, self.forward, entries, max_length))
        try:
            avg = total_lengths/entries
        except:
            avg = 0
        self.lg.info(f"{self.ext_id}: average_neighborhood_degree={avg} ({total_lengths}/{entries})") # Wrong!!!!!!!!!!!!!!!!!!!!!

        self.lg.info(f"{self.ext_id}: forward = {self.forward}")

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
#    def am_i_a_monitor(self):
#        return self.number_of_peers < self.number_of_monitors

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
