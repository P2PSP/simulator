"""
@package simulator
peer_dbs module
"""

# DBS (Data Broadcasting Set) layer

# DBS peers receive chunks from the splitter and other peers, and
# resend them, depending on the forwarding requests performed by the
# peers. In a nutshell, if a peer X wants to receive from peer Y
# the chunks from origin Z, X must request it to Y, explicitally.

import time
import struct
import logging
import random
from threading import Thread
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import Simulator_socket as socket
from .simulator_stuff import hash

class Peer_DBS(sim):
    # Peers interchange chunks. If a peer A sends MAX_CHUNK_DEBT more
    # chunks to a peer B than viceversa, A stops sending to B. -> To FCS
    MAX_CHUNK_DEBT = 16

    # In chunks. Number of buffered chunks before starting the
    # playback.
    BUFFER_SIZE = 32

    # Positions of each field (chunk, chunk_number, origin) in a
    # buffer's message.
    CHUNK_NUMBER = 0
    CHUNK_DATA = 1
    ORIGIN = 2

    MAX_DEGREE = 5

    # S I M U L A T I O N
    #                  |
    #                  v
    def __init__(self, id, name, loglevel):
        self.lg = logging.getLogger(name)
        self.lg.setLevel(loglevel)
        self.lg.critical('Critical messages enabled.')
        self.lg.error   ('Error messages enabled.')
        self.lg.warning ('Warning message enabled.')
        self.lg.info    ('Informative message enabled.')
        self.lg.debug   ('Low-level debug message enabled.')

        # Peer identification. Depending on the simulation degree, it
        # can be a simple string or an endpoint.
        self.id = None

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
        self.number_of_monitors = 0

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
        # X, in a burst, when a chunk arrives.
        self.pending = {}

        # Counters of sent - recived chunks, by peer. Every time a
        # peer X sends a chunk to peer Y, X increments debt[Y] and Y
        # decrements debt[X] (and viceversa). If a X.debt[Y] >
        # MAX_CHUNK_DEBT, X will stop sending more chunks to Y. It
        # should be implemented in FCS.
        self.debt = {}
        # self.debt[self.id] = 0

        self.team = []

        # Sent and received chunks.
        self.sendto_counter = 0  # Unused

        # S I M U L A T I O N
        self.received_chunks = 0

        # The longest message expected to be received: chunk_number,
        # chunk, IP address of the origin peer, and port of the origin
        # peer.
        self.max_pkg_length = struct.calcsize("isli")

        self.neighbor_index = 0

        # Played or lost
        self.number_of_chunks_consumed = 0

        # S I M U L A T I O N
        self.losses = 0

        # S I M U L A T I O N
        self.played = 0

        # S I M U L A T I O N
        self.chunks_before_leave = 0

        # S I M U L A T I O N
        self.link_failure_prob = 0.0

        # S I M U L A T I O N
        self.max_degree = self.MAX_DEGREE
        
        self.rounds_counter = 0

        self.chunk_number_delta = 0
        
        self.lg.debug("{}: DBS initialized".format(self.id))

    def listen_to_the_team(self):
        self.team_socket = socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.team_socket.bind(self.id)
        self.lg.debug("{}: listening to {}".format(self.ext_id, self.id))
        self.say_hello(self.splitter) # Only works for cone NATs
        #self.team_socket.bind(("", self.id[1]))
        #self.team_socket.settimeout(100)

    def set_splitter(self, splitter):
        self.splitter = splitter

    # def recv(self, fmt):
    #    msg_length = struct.calcsize(fmt)
    #    msg = self.splitter_socket.recv(msg_length)
    #    while len(msg) < msg_length:
    #        msg += self.splitter_socket.recv(msg_length - len(msg))
    #    return struct.unpack(fmt)[0]

    def receive_public_endpoint(self):
        msg_length = struct.calcsize("li")
        msg = self.splitter_socket.recv(msg_length)
        self.public_endpoint = struct.unpack("li", msg)[0]
        self.lg.debug("{}: public endpoint = {}".format(self.id, self.public_endpoint))
    
    def receive_buffer_size(self):
        # self.buffer_size = self.splitter_socket.recv("H")
        # self.buffer_size = self.recv("H")
        msg_length = struct.calcsize("H")
        msg = self.splitter_socket.recv(msg_length)
        self.buffer_size = struct.unpack("H", msg)[0]
        self.lg.debug("{}: buffer size = {}".format(self.id, self.buffer_size))

        # S I M U L A T I O N
        self.sender_of_chunks = [""] * self.buffer_size

    def receive_the_number_of_peers(self):
        msg_length = struct.calcsize("H")
        msg = self.splitter_socket.recv(msg_length)
        self.number_of_monitors = struct.unpack("H", msg)[0]
        self.lg.debug("{}: number of monitors = {}".format(self.id, self.number_of_monitors))

        msg_length = struct.calcsize("H")
        msg = self.splitter_socket.recv(msg_length)
        self.number_of_peers = struct.unpack("H", msg)[0]
        self.lg.debug("{}: number of peers = {}".format(self.id, self.number_of_peers))

        self.peer_number = self.number_of_peers
        self.ext_id = ("%03d" % self.peer_number, self.id[0], "%5d" % self.id[1])
        self.lg.debug("{}: peer number = {}".format(self.ext_id, self.number_of_peers))

    def say_hello(self, peer):
        msg = struct.pack("i", Common.HELLO)
        self.team_socket.sendto(msg, peer)
        self.lg.debug("{}: sent [hello] to {}".format(self.ext_id, peer))

    def receive_the_list_of_peers(self):
        self.index_of_peer = {}
        peers_pending_of_reception = self.number_of_peers
        msg_length = struct.calcsize("li")
        counter = 0

        # Peer self.id will forward by default all chunks originated
        # at itself.
        self.forward[self.id] = []
        
        while peers_pending_of_reception > 0:
            msg = self.splitter_socket.recv(msg_length)
            peer = struct.unpack("li", msg)
            peer = (socket.int2ip(peer[0]),peer[1])
            self.team.append(peer)
            self.forward[self.id].append(peer)
            self.index_of_peer[peer] = counter

            # S I M U L A T O R
            if counter >= self.number_of_monitors: # Monitors never are isolated
                r = random.random()
                if r <= self.link_failure_prob:
                    self.team_socket.isolate(self.id, peer)
                    self.lg.critical("{}: {} isolated of {}".format(self.ext_id, self.id, peer))
                
            self.say_hello(peer)
            self.lg.debug("{}: peer {} is in the team".format(self.ext_id, peer))
            counter += 1
            peers_pending_of_reception -= 1

        self.lg.debug("{}: forward={} pending={}".format(self.ext_id, self.forward, self.pending))
        
            # self.lg.debug("{}: sent [hello] to {} peers".format(self.id, self.number_of_peers))

            # Incoming peers populate their forwarding tables when chunks
            # are received from other peers. The rest of peers populate
            # their forwarding tables with received [hello]
            # messages. Randomization could be produced at this instant in
            # the splitter, if necessary.

    # S I M U L A T I O N
    def send_peer_type(self):
        if(self._id[0:2]=='MP'):
            msg = struct.pack('H',2)    # Malicious Peer
        elif(self._id[0]=='M'):
            msg = struct.pack('H',0)    # Monitor Peer
        else:
            msg = struct.pack('H',1)    # Regular Peer
        self.splitter_socket.send(msg)

    if __debug__:
        # S I M U L A T I O N
        def map_peer_type(self,real_id):
            if sim.FEEDBACK:
                if self._id[0] == 'M':
                    if self._id[1] == 'P':
                        sim.FEEDBACK["DRAW"].put(("MAP",','.join(map(str,real_id)),"MP"))
                    else:
                        sim.FEEDBACK["DRAW"].put(("MAP",','.join(map(str,real_id)),"M"))
                else:
                    sim.FEEDBACK["DRAW"].put(("MAP",','.join(map(str,real_id)),"P"))    

    def connect_to_the_splitter(self, monitor_port):
        self.lg.debug("{}: connecting to the splitter at {}".format(self.id, self.splitter))
        self.splitter_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.splitter_socket.set_id(self.id) # Ojo, simulation dependant
        #host = socket.gethostbyname(socket.gethostname())
        self.splitter_socket.bind(('', monitor_port))

        try:
            self.splitter_socket.connect(self.splitter)
        except ConnectionRefusedError as e:
            self.lg.error("{}: {}".format(self.id, e))
            raise

        # The index for pending[].
        self.id = self.splitter_socket.getsockname()
        print("{}: I'm a peer".format(self.id))
        #self.neighbor = self.id
        #print("self.neighbor={}".format(self.neighbor))
        #self.pending[self.id] = []

        if __debug__:
            # S I M U L A T I O N
            self.map_peer_type(self.id); # Maybe at the end of this
                                         # function to be easely extended
                                         # in the peer_dbs_sim class.

        self.lg.debug("{}: connected to the splitter".format(self.id))

    def old_connect_to_the_splitter(self):
        self.lg.debug("{}: connecting to the splitter at {}".format(self.id, self.splitter))
        self.splitter_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.splitter_socket.set_id(self.id) # Ojo, simulation dependant
        #host = socket.gethostbyname(socket.gethostname())
        #self.splitter_socket.bind((host,0))

        try:
            self.splitter_socket.connect(self.splitter)
        except ConnectionRefusedError as e:
            self.lg.error("{}: {}".format(self.id, e))
            raise

        # The index for pending[].
        self.id = self.splitter_socket.getsockname()
        print("{}: I'm a peer".format(self.id))
        #self.neighbor = self.id
        #print("self.neighbor={}".format(self.neighbor))
        #self.pending[self.id] = []

        if __debug__:
            # S I M U L A T I O N
            self.map_peer_type(self.id); # Maybe at the end of this
                                         # function to be easely extended
                                         # in the peer_dbs_sim class.

        self.lg.debug("{}: connected to the splitter".format(self.id))

    # Why?
    def send_ready_for_receiving_chunks(self):
        # self.splitter_socket.send(b"R", "s") # R = Ready
        msg = struct.pack("s", b"R")
        self.splitter_socket.send(msg)
        self.lg.debug("{}: sent {} to {}".format(self.ext_id, "[ready]", self.splitter))

    def is_a_control_message(self, message):
        if message[0] < 0:
            return True
        else:
            return False

    def prune_origin(self, chunk_number, peer):
        msg = struct.pack("ii", Common.PRUNE, chunk_number)
        self.team_socket.sendto(msg, peer)
        self.lg.info("{}: sent [prune {}] to {}".format(self.ext_id, chunk_number, peer))

    def buffer_new_chunk(self, chunk_number, chunk_data, origin, sender):
        self.lg.debug("{}: received chunk {} from {}".format(self.ext_id, (chunk_number, chunk_data, origin), sender))
        # New chunk. (chunk_number, chunk, origin) -> buffer[chunk_number]
        self.chunks[chunk_number % self.buffer_size] = (chunk_number, chunk_data, origin)

    def update_pendings(self, origin, chunk_number):
        # The peer has received a new chunk, and the chunk has an
        # origin. In the forward table, each chunk has a list of
        # origin peers and for each one, a list of destination
        # peers. All peers, by default, has in forward[] an entry with
        # their end-point, that by default, points to the list of
        # neighbors. So, when a peer has received a chunk with a
        # origin the peer itself, it will forward that chunk (after
        # updating the pending structure) to all its neighbors. The
        # forwarding table can have more entries, created by [request]
        # messages. So, when a peer receives a chunk (from the
        # splitter or another peer), and the origin of the chunk is in
        # the forwarding table, the chunk should be added to each
        # entry of pending that there is in the list of peers pointed
        # by the origin in the forward table.
        
        # A new chunk has been received from an origin. For all peers
        # in forward[origin] the chunk (number) is appended. 
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
            self.lg.debug("{}: appended {} to pending[{}]".format(self.ext_id, chunk_number, peer))
        self.lg.debug("{}: pending={}".format(self.ext_id, self.pending))
        #self.lg.debug("{}: forward[{}]={}".format(self.ext_id, origin, self.forward[origin]))

    def add_new_forwarding_rule(self, peer, neighbor):
        try:
            if neighbor not in self.forward[peer]:
                self.lg.debug("{}: {} adding new neighbor {}".format(self.ext_id, peer, neighbor))
                self.forward[peer].append(neighbor)
                self.pending[neighbor] = []
        except KeyError:
            self.forward[peer] = [neighbor]
            self.pending[neighbor] = []

    def compose_message(self, chunk_number):
        chunk_position = chunk_number % self.buffer_size
        chunk = self.chunks[chunk_position]
        stored_chunk_number = chunk[self.CHUNK_NUMBER]
        chunk_data = chunk[self.CHUNK_DATA]
        chunk_origin_IP = chunk[self.ORIGIN][0]
        chunk_origin_port = chunk[self.ORIGIN][1]
        content = (stored_chunk_number, chunk_data, socket.ip2int(chunk_origin_IP), chunk_origin_port)
        packet = struct.pack("isli", *content)
        return packet
            
    def send_chunk(self, chunk_number, peer):
        try:
            msg = self.compose_message(chunk_number)
            #msg = struct.pack("isli", stored_chunk_number, chunk_data, socket.ip2int(chunk_origin_IP), chunk_origin_port)
            self.team_socket.sendto(msg, peer)
            self.sendto_counter += 1
            #self.lg.debug("{}: sent chunk {} (with origin {}) to {}".format(self.ext_id, chunk_number, (chunk_origin_IP, chunk_origin_port), peer))
        except TypeError:
            self.lg.warning("{}: chunk {} not sent because it was lost".format(self.ext_id, chunk_number))
            pass
 
    def send_chunks(self):
        # When peer X receives a chunk, X selects the next
        # entry pending[E] (with one or more chunk numbers),
        # sends the chunk with chunk_number C indicated by
        # pending[E] to E, and removes C from pending[E]. If
        # in pending[E] there are more than one chunk
        # (number), all chunks are sent in a burst. E should
        # be selected to sent first to those peers that we
        # want to forward us chunks not originated in them.
        #   if self.neighbor in self.pending:
        self.lg.debug("{}: send_chunks (begin) neighbor={} pending[{}]={}".format(self.ext_id, self.neighbor, self.neighbor, self.pending[self.neighbor]))
        for chunk_number in self.pending[self.neighbor]:
            self.lg.debug("{}: send_chunks sel_chunk={} to neighbor={}".format(self.ext_id, chunk_number, self.neighbor))
            self.send_chunk(chunk_number, self.neighbor)
        self.pending[self.neighbor] = []
        #for chunk_number in self.pending[self.neighbor]:
        #    self.pending[self.neighbor].remove(chunk_number)
        self.lg.debug("{}: send_chunks (end) neighbor={} pending[{}]={}".format(self.ext_id, self.neighbor, self.neighbor, self.pending[self.neighbor]))

    def process_request(self, chunk_number, sender):

        # If a peer X receives [request Y] from peer Z, X will
        # append Z to forward[Y.origin].

        origin = self.chunks[chunk_number % self.buffer_size][self.ORIGIN]

        self.lg.debug("{}: received [request {}] from {} (origin={}, forward={})".format(self.ext_id, chunk_number, sender, origin, self.forward))

        if origin != None:
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
            
            self.lg.debug("{}: chunks from {} will be sent to {}".format(self.ext_id, origin, sender))

            if __debug__:
                # S I M U L A T I O N
                if sim.FEEDBACK:
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str,sender)) ))
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", ','.join(map(str,self.id)), ','.join(map(str,sender))))
        else:
            # Otherwise, I can't help.
            if __debug__:
                self.lg.debug("{}: request received from {}, but I haven't the requested chunk {}".format(self.ext_id, sender, chunk_number))
            #continue
        
        # if origin in self.forward:
        #     #self.lg.debug("{}: aqui (sender={} forward={})".format(self.id, sender, self.forward))
        #     if sender not in self.forward[origin]:
        #         # Insert sender in the forwarding table.
        #         self.forward[origin].append(sender)
        #         self.lg.debug("{}: chunks from {} will be sent to {}".format(self.ext_id, origin, sender))

        #         # S I M U L A T I O N
        #         if sim.FEEDBACK:
        #             sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str,sender)) ))
        #             sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", ','.join(map(str,self.id)), ','.join(map(str,sender))))
                    
        # else:
        #     if origin != None:
        #         self.forward[origin] = [sender]
        #         self.lg.debug("{}: chunks from {} will be sent (2) to {}".format(self.ext_id, origin, sender))

        self.lg.debug("{}: chunk={} origin={} forward={}".format(self.ext_id, self.chunks[chunk_number % self.buffer_size], origin, self.forward))
        self.lg.debug("{}: length_forward={} forward={}".format(self.ext_id, len(self.forward), self.forward))
        
    def process_prune(self, chunk_number, sender):
        self.lg.debug("{}: received [prune {}] from {}".format(self.ext_id, chunk_number, sender))
        chunk = self.chunks[chunk_number % self.buffer_size]
        # Notice that chunk_number must be stored in the buffer
        # because it has been sent to a neighbor.
        origin = chunk[self.ORIGIN]
        if origin in self.forward:
            if sender in self.forward[origin]:
                try:
                    self.forward[origin].remove(sender)
                    self.lg.debug("{}: {} removed from forward[origin={}]={}".format(self.ext_id, sender, origin, self.forward[origin]))
                except ValueError:
                    self.lg.error("{}: failed to remove peer {} from forward table {} for origin {} ".format(self.id, sender, self.forward[origin], origin))
                if len(self.forward[origin])==0:
                    del self.forward[origin]

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

        if sender not in self.forward[self.id]:
            self.forward[self.id].append(sender)
            self.pending[sender] = []
            self.lg.info("{}: inserted {} in forward[{}] by [hello] from {} (forward={})".format(self.ext_id, sender, self.id, sender, self.forward))
            self.debt[sender] = 0

            if __debug__:
                # S I M U L A T I O N
                if sim.FEEDBACK:
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str,sender))))
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", ','.join(map(str,self.id)), ','.join(map(str,sender))))
        self.team.append(sender)

    def process_goodbye(self, sender):
        self.lg.debug("{}: received [goodbye] from {}".format(self.ext_id, sender))

        if sender == self.splitter:
            self.lg.debug("{}: received [goodbye] from splitter".format(self.ext_id))
            self.waiting_for_goodbye = False
            self.player_connected = False

        else:
            try:
                self.team.remove(sender)
            except ValueError:
                pass
            for peers_list in self.forward.values():
                if sender in peers_list:
                    self.lg.info("{}: {} removing from {}".format(self.ext_id, sender, peers_list))
                    try:
                        peers_list.remove(sender)
                    except ValueError:
                        self.lg.error("{}: : failed to remove peer {} from {}".format(self.ext_id, sender, peers_list))
                    #try:
                    #    del self.debt[sender]
                    #except KeyError:
                    #    self.lg.debug("{}: {} is not it {}".format(self.ext_id, sender, self.debt))
                    #print("{}: -----------> {}".format(self.ext_id, len(peers_list)))
                    #if len(peers_list)==0:
                    #    del peers_list
            # sim.FEEDBACK["DRAW"].put(("O", "Node", "OUT", ','.join(map(str,sender))))     # To remove ghost peer

    # DBS peer's logic
    def process_unpacked_message(self, message, sender):

        chunk_number = message[self.CHUNK_NUMBER]

        if chunk_number >= 0:

            # We have received a chunk.
            chunk_data = message[self.CHUNK_DATA]
            origin = message[self.ORIGIN]

            # Compute deltas
            self.chunk_number_delta = chunk_number - self.chunk_number_delta
            #self.chunk_number_delta = chunk_number - self.prev_received_chunk
            self.lg.info("{}: delta of chunk {} is {}".format(self.ext_id, chunk_number, self.chunk_number_delta))
            self.chunk_number_delta = chunk_number

            if __debug__:
                # S I M U L A T I O N
                if sender == self.splitter:
                    if self.played > 0 and self.played >= self.number_of_peers:
                        CLR = self.losses / (self.played + self.losses) # Chunk Loss Ratio
                        if sim.FEEDBACK:
                            sim.FEEDBACK["DRAW"].put(("CLR", ','.join(map(str,self.id)), CLR))
                        #self.losses = 0 # Ojo, puesto a 0 para calcular CLR
                        #self.played = 0 # Ojo, puesto a 0 para calcular CLR

            # 1. Store or report duplicates
            if self.chunks[chunk_number % self.buffer_size][self.CHUNK_NUMBER] == chunk_number:
                # Duplicate chunk. Ignore it and warn the sender to
                # stop sending more chunks from the origin of the received
                # chunk "chunk_number".
                self.lg.debug("{}: duplicate chunk {} from {} (the first one was sent by {}) BUFFER={}".format(self.ext_id, chunk_number, sender, self.chunks[chunk_number % self.buffer_size][self.ORIGIN], self.chunks))
                self.prune_origin(chunk_number, sender)
            else:
                self.buffer_new_chunk(chunk_number, chunk_data, origin, sender)
                
                # Showing buffer
                buf = ""
                for i in self.chunks:
                    if i[self.CHUNK_NUMBER] != -1:
                        try:
                            peer_number = self.index_of_peer[i[self.ORIGIN]]
                        except KeyError:
                            self.index_of_peer[i[self.ORIGIN]] = self.number_of_peers
                            peer_number = self.number_of_peers
                            self.number_of_peers += 1
                        buf += hash(peer_number)
                    else:
                        buf += " "
                self.lg.debug("{}: buffer={}".format(self.ext_id, buf))

                # S I M U L A T I O N
                self.received_chunks += 1
                if (self.received_chunks >= self.chunks_before_leave):
                    self.player_connected = False
#                self.sender_of_chunks = []
#                for i in self.chunks:
#                    if i[self.CHUNK_NUMBER] != -1:
#                        self.sender_of_chunks.append(','.join(map(str,i[self.ORIGIN])))
#                    else:
#                        self.sender_of_chunks.append("")
#                if sim.FEEDBACK:
#                    sim.FEEDBACK["DRAW"].put(("B", ','.join(map(str,self.id)), ":".join(self.sender_of_chunks)))

                if sender == self.splitter:
                    # if len(self.forward[self.id]) > 0:
                    #self.update_pendings(self.id, chunk_number)
                    self.rounds_counter += 1
                    for peer, peer_list in self.forward.items():
                        if len(peer_list) > 0:
                            buf = len(peer_list)*"#"
                            self.lg.debug("{}: degree({})) {}".format(self.ext_id, peer, buf))
                else:
                    #if sender in self.debt:
                    #    self.debt[sender] -= 1
                    #else:
                    #    self.debt[sender] = -1
                    # Usar mejor técnica de ir dividiendo entre 2 cada round
                    #if self.neighbor is None:  # Quizás se pueda quitar!!!!
                    #self.neighbor = sender
                    #try:
                    #    if sender not in self.forward[self.id]:
                    #        self.forward[self.id].append(sender)
                    #        self.pending[sender] = []
                    #except KeyError:
                    #    self.forward[self.id] = [sender]
                    #    self.pending[sender] = []
                    self.add_new_forwarding_rule(self.id, sender)
                    self.lg.debug("{}: forward={}".format(self.ext_id, self.forward))
                    #for peer in self.forward:
                #print("origin={} forward={}".format(origin, self.forward))
                if origin in self.forward:
                    self.update_pendings(origin, chunk_number)
                # When a peer X receives a chunk (number) C with origin O,
                # for each peer P in forward[O], X performs
                # pending[P].append(C).
                #if origin in self.forward:  # True: #len(self.forward[origin]) > 0: #True: #origin != self.id:
                #    for P in self.forward[origin]:
                        #if P in self.pending:
                #        self.pending[P].append(chunk_number)
                        #else:
                        #    self.pending[P] = []
                        #    self.pending[P].append(chunk_number)

                    #                        if P in self.pending:
                    #                            self.lg.debug("{}: oooooooo {}".format(self.id, P))
                    #                            self.pending[P].append(chunk_number)
                    #                        elif len(self.pending) == 0:
                    #                            self.pending[P] = []
                    #                            self.pending[P].append(chunk_number)

                #self.lg.debug("{}: origin={} forward={} pending={}".format(self.ext_id, origin, self.forward, self.pending))

                if len(self.pending) > 0:
                    self.neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
                    self.send_chunks()
                    self.neighbor_index = list(self.pending.keys()).index(self.neighbor) + 1
                
                self.lg.debug("{}: debt={}".format(self.ext_id, self.debt))

        else:  # message[CHUNK_NUMBER] < 0

            if chunk_number == Common.REQUEST:
                self.process_request(message[1], sender)
            elif chunk_number == Common.PRUNE:
                self.process_prune(message[1], sender)
            elif chunk_number == Common.HELLO:
                #if len(self.forward[self.id]) < self.max_degree:
                self.process_hello(sender)
            elif chunk_number == Common.GOODBYE:
                self.process_goodbye(sender)
            else:
                self.lg.info("{}: unexpected control chunk of index={}".format(self.ext_id, chunk_number))
        return (chunk_number, sender)

    def receive_packet(self):
        #print("{}".format(self.max_pkg_length))
        try:
            return self.team_socket.recvfrom(self.max_pkg_length)
        except self.team_socket.timeout:
            raise
    
    def process_message(self):
        try:
            pkg, sender = self.receive_packet()
            # self.lg.debug("{}: received {} from {} with length {}".format(self,id, pkg, sender, len(pkg)))
            if len(pkg) == self.max_pkg_length:
                message = struct.unpack("isli", pkg) # Data message:
                                                     # [chunk number,
                                                     # chunk, origin
                                                     # (address and port)]
                message = message[self.CHUNK_NUMBER], \
                          message[self.CHUNK_DATA], \
                          (socket.int2ip(message[self.ORIGIN]),message[self.ORIGIN+1])
            elif len(pkg) == struct.calcsize("iii"):
                message = struct.unpack("iii", pkg)  # Control message:
                                                     # [control, parameter]
            elif len(pkg) == struct.calcsize("ii"):
                message = struct.unpack("ii", pkg)  # Control message:
                                                    # [control, parameter]
            else:
                message = struct.unpack("i", pkg)  # Control message:
                                                   # [control]
            return self.process_unpacked_message(message, sender)
        except self.team_socket.timeout:
            #self.say_goodbye(self.splitter)
            #self.say_goodbye_to_the_team()
            raise
        #    return (0, self.id)
        
    def request_chunk(self, chunk_number, peer):
        msg = struct.pack("ii", Common.REQUEST, chunk_number)
        self.team_socket.sendto(msg, peer)
        self.lg.info("{}: [request {}] sent to {}".format(self.ext_id, chunk_number, peer))

    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number % self.buffer_size][self.CHUNK_DATA] == b'C':
            self.chunks[chunk_number % self.buffer_size] = (-1, b'L', None)
            self.played += 1
        else:
            self.losses += 1
            self.lg.critical("{}: lost chunk! {} (losses = {})".format(self.ext_id, chunk_number, self.losses))

            # The chunk "chunk_number" has not been received on time
            # and it is quite probable that is not going to change
            # this in the near future. The action here is to request
            # the lost chunk to one or more peers using a [request
            # <chunk_number>]. If after this, I will start receiving
            # duplicate chunks, then a [prune <chunk_number>] should
            # be sent to those peers which send duplicates.

            # Request the chunk to the origin peer of the last received chunk.
            #i = self.prev_received_chunk
            #destination = self.chunks[i % self.BUFFER_SIZE][self.ORIGIN]
            #while destination == None:
            #    i += 1
            #    destination = self.chunks[i % self.BUFFER_SIZE][self.ORIGIN]
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

            self.request_chunk(chunk_number, random.choice(self.team))
            
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
            self.chunk_to_play = (self.chunk_to_play + 1) % Common.MAX_CHUNK_NUMBER
        if ((self.prev_received_chunk % Common.MAX_CHUNK_NUMBER) < last_received_chunk):
            self.prev_received_chunk = last_received_chunk

    def buffer_and_play(self):
        last_received_chunk = -1
        while (last_received_chunk < 0) and (self.player_connected):
            try:
                (last_received_chunk, _) = self.process_message()
            except self.team_socket.timeout:
                self.player_connected = False
                self.waiting_for_goodbye = False
                self.lg.critical("{}: timeout!".format(self.ext_id))
                break
#        (last_received_chunk, _) = self.process_message()
#        while last_received_chunk < 0:
#            if self.player_connected == False:
#                break
#            (last_received_chunk, _) = self.process_message()

        self.play_next_chunks(last_received_chunk)

    # To be placed in peer_dbs_sim ?
    def compose_goodbye_message(self):
        msg = struct.pack("iii", Common.GOODBYE, self.number_of_chunks_consumed, self.losses)
        self.lg.debug("{}: played={}".format(self.ext_id, self.number_of_chunks_consumed))
        self.lg.debug("{}: losses={}".format(self.ext_id, self.losses))
        return msg

    # To be here
    # def compose_goodbye_message(self):
    #    msg = struct.pack("i", Common.GOODBYE)
    #    return msg

    def say_goodbye(self, peer):
        # self.team_socket.sendto(Common.GOODBYE, "i", peer)
        msg = self.compose_goodbye_message()
        self.team_socket.sendto(msg, peer)
        self.lg.debug("{}: sent [goodbye] to {}".format(self.ext_id, peer))

    def say_goodbye_to_the_team(self):
        for origin, peer_list in self.forward.items():
            for peer in peer_list:
                self.say_goodbye(peer)

        # Next commented lines freeze the peer (in a receive() call)
        # while (all(len(d) > 0 for d in self.pending)):
        #     self.process_message()

        self.ready_to_leave_the_team = True
        self.lg.debug("{}: said goodbye to the team".format(self.ext_id))

    def buffer_data(self):
        # Receive a chunk.
        (chunk_number, sender) = self.process_message()
        while chunk_number < 0:
            (chunk_number, sender) = self.process_message()
            if self.player_connected == False:
                break
        # self.neighbor = sender

        # The first chunk to play is the firstly received chunk (which
        # probably will not be the received chunk with the smallest
        # index).
        self.chunk_to_play = chunk_number

        self.lg.debug("{}: position in the buffer of the first chunk to play = {}".format(self.ext_id, self.chunk_to_play))

        while (chunk_number < self.chunk_to_play) or (((chunk_number - self.chunk_to_play) % self.buffer_size) < (self.buffer_size // 2)):
            (chunk_number, _) = self.process_message()
            if not self.player_connected:
                break
            while (chunk_number < self.chunk_to_play):
                (chunk_number, _) = self.process_message()
                if not self.player_connected:
                    break
        self.prev_received_chunk = chunk_number

    def run(self):
        for i in range(self.buffer_size):
            self.chunks.append((-1, b'L', None))  # L == Lost ??

        start_time = time.time()
        self.buffer_data()
        buffering_time = time.time() - start_time
        print("{}: buffering time (main latency) = {}".format(self.ext_id, buffering_time))
        while (self.player_connected or self.waiting_for_goodbye):
            self.buffer_and_play()
            # The goodbye messages sent to the splitter can be
            # lost. Therefore, it's a good idea to keep sending
            # [goodbye]'s to the splitter until the [goodbye] from the
            # splitter arrives.
            if not self.player_connected:
                break
        self.say_goodbye(self.splitter)
        self.say_goodbye_to_the_team()

        # Send pending chunks
        for peer, chunks in self.pending.items():
            for chunk in chunks:
                self.send_chunk(chunk, peer)

        # Print some statistics
        total_lengths = 0
        #max_length = 0
        entries = 0
        for origin, peers_list in self.forward.items():
            self.lg.debug("{}: goodbye forward[{}]={} {}".format(self.ext_id, origin, peers_list, len(peers_list)))
            total_lengths += len(peers_list)
            if(len(peers_list)>0): # This should not be necessary
                entries += 1
            #if max_length < len(peers_list):
            #    max_length = len(peers_list)
        #print("{}: forward={} forward_entries={} max_length={}".format(self.ext_id, self.forward, entries, max_length))
        avg = total_lengths/entries
        print("{}: average_neighborhood_degree={} ({}/{})".format(self.ext_id, avg, total_lengths, entries))

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
