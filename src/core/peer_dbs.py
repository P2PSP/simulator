"""
@package simulator
peer_dbs module
"""

# DBS (Data Broadcasting Set) layer

# DBS peers receive chunks from the splitter and other peers, and
# resend them, depending on the forwarding requests performed by the
# peers. In a nutshell, if a peer X wants to receive from peer Y
# the chunks from origin Z, X must request it to Y, explicitally.

from threading import Thread
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import Simulator_socket as socket
from .simulator_stuff import lg
import sys
import struct

class Peer_DBS(sim):

    # Peers interchange chunks. If a peer A sends MAX_CHUNK_DEBT more
    # chunks to a peer B than viceversa, A stops sending to B.
    MAX_CHUNK_DEBT = 128

    # In chunks. Number of buffered chunks before starting the
    # playback.
    BUFFER_SIZE = 32

    # Positions of each field (chunk, chunk_number, origin) in a
    # buffer's cell.
    CHUNK_NUMBER = 0
    CHUNK        = 1
    ORIGIN       = 2
    
    def __init__(self, id):

        # Peer identification. Depending on the simulation degree, it
        # can be a simple string or an endpoint.
        self.id = id

        # Chunk currently played.
        self.played_chunk = 0

        # Buffer of chunks (used as a circular queue).
        self.chunks = []

        # While True, keeps the peer alive.
        self.player_alive = True

        # Counters of sent - recived chunks, by peer. Every time a peer
        # X sends a chunk to peer Y, X increments debt[Y] and Y
        # decrements debt[X] (and viceversa). If a X.debt[Y] >
        # MAX_CHUNK_DEBT, X will stop sending more chunks to Y.
        self.debt = []

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
        self.number_of_peers = 0

        # A flag that when True, fires the leaving process.
        self.ready_to_leave_the_team = False

        # Forwarding rules of chunks, indexed by origins. If a peer
        # has an entry forward[Y]={..., Z, ...}, every chunk received
        # from origin (endpoint) Y will be forwarded towards
        # (index) Z.
        self.forward = []

        # List of pending chunks (numbers) to be sent to peers. Por
        # example, if pending[5] = {1,2,3}, the chunks stored in
        # entries 1, 2, and 3 of the buffer will be sent to the peer
        # (with index) 5.
        self.pending = []
        
        # Peers start feeding the first neighbor peer self.forward[0].
        self.neighbor = None
  
        # Sent and received chunks.
        self.sendto_counter = 0
        self.received_chunks = 0

        # The longest message it is expected to receive.
        self.max_msg_length = struct.calcsize("isi")
        
        lg.info("{}: DBS initialized".format(self.id))

        if __debug__:
            self.losses = 0
            self.played = 0
            self.number_of_chunks_consumed = 0
            self.chunks_before_leave = 0

    def listen_to_the_team(self):
        self.team_socket = socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        #self.team_socket.set_id(self.id) # ojo, simulation dependent
        #self.team_socket.set_max_packet_size(["isi", "i", "ii"])
        # "chunk_index, chunk, origin", "[hello]/[goodbye]",  "[request <chunk>]/[prune <chunk>]"
        self.team_socket.bind(self.id)

    def set_splitter(self, splitter):
        self.splitter = splitter

    def recv(self, fmt):
        msg_length = struct.calcsize(fmt)
        msg = self.splitter_socket.recv(msg_length)
        while len(msg) < msg_length:
            msg += self.splitter_socket.recv(msg_length - len(msg))
        return struct.unpack(fmt)[0]
        
    def receive_buffer_size(self):
        #self.buffer_size = self.splitter_socket.recv("H")
        self.buffer_size = self.recv("H")
        lg.info("{}: buffer size = {}".format(self.id, self.buffer_size))
        if __debug__:
            self.sender_of_chunks = [""]*self.buffer_size

    def receive_the_number_of_peers(self):
        msg_length = struct.calcsize("H")
        msg = self.splitter_socket.recv(msg_length)
        self.number_of_monitors = struct.unpack("H")[0]
        lg.info("{}: number of monitors = {}".format(self.id, self.number_of_monitors))
        
        msg_length = struct.calcsize("H")
        msg = self.splitter_socket.recv(msg_length)
        self.number_of_peers = struct.unpack("H")[0]
        lg.info("{}: number of peers = {}".format(self.id, self.number_of_peers))
        
    def say_hello(self, peer):
        #self.team_socket.sendto(Common.HELLO, "i", peer)
        msg = struct.pack("i", Common.HELLO)
        self.team_socket.sendto(msg, peer)
        lg.info("{}: [hello] sent to {}".format(self.id, peer))

    def say_goodbye(self, index):
        #self.team_socket.sendto(Common.GOODBYE, "i", peer)
        msg = struct.pack("i", Common.GOODBYE)
        self.team_socket.sendto(msg, peer)
        lg.info("{}: [goodbye] sent to {}".format(self.id, peer))

    def receive_the_list_of_peers(self):
        peers_pending_of_reception = self.number_of_peers
        msg_length = struct.calcsize("6s")
        while peers_pending_of_reception > 0:
            peer = self.splitter_socket.recv(msg_length)
            self.say_hello(peer)
            peers_pending_of_reception -= 1

        lg.info("{}: sent [hello] to {} peers".format(self.id, self.number_of_peers))

        # Incoming peers populate their forwarding tables when chunks
        # are received from other peers. The rest of peers populate
        # their forwarding tables with received [hello]
        # messages. Randomization could be produced at this instant in
        # the splitter, if necessary.

    def connect_to_the_splitter(self):
        self.splitter_socket = socket(socket.AF_UNIX, socket.SOCK_STREAM)
        #self.splitter_socket.set_id(self.id) # Ojo, simulation dependant
        self.splitter_socket.bind(self.id)
        try:
            self.splitter_socket.connect(self.splitter)
        except ConnectionRefusedError as e:
            lg.error("{}: {}".format(self.id, e))
            raise

        lg.info("{}: connected to the splitter".format(self.id))

    def send_ready_for_receiving_chunks(self):
        #self.splitter_socket.send(b"R", "s") # R = Ready
        msg = struct.pack("s", b"R")
        self.splitter_socket.sendto(msg)
        lg.info("{}: sent {} to {}".format(self.id, "[ready]", self.splitter))

    def send_chunk(self, chunk_index, peer):
        #self.team_socket.sendto(self.chunks[chunk_number], "isi", peer)
        msg = struct.pack("isi", chunks[chunk_number])
        self.team_socket.sendto(msg, peer)
        self.sendto_counter += 1

    def is_a_control_message(self, message):
        if message[0] < 0:
            return True
        else:
            return False

    def prune_origin(self, chunk_number, peer):
        #self.team_socket.sendto((Common.PRUNE, chunk_number), "ii", peer)
        msg = struct.pack("ii", (Common.PRUNE, chunk_number))
        self.team_socket.sendto(packed_msg, peer)
        lg.info("{}: [prune {}] sent to {}".format(self.id, chunk_number, peer))

    def process_message(self, message, sender):

        if __debug__:
            if not self.is_a_control_message(message) and self.endpoint[sender] == self.splitter:
                if self.played > 0 and self.played >= len(self.peer_list):
                    clr = self.losses/self.played
                    sim.FEEDBACK["DRAW"].put(("CLR", self.id, clr))
                    self.losses = 0
                    self.played = 0

        chunk_number = message[self.CHUNK_NUMBER]

        if chunk_number >= 0:

            # We have received a chunk.
            if (self.chunks[chunk_number % self.buffer_size][self.CHUNK_NUMBER]) == chunk_number:
                
                # Duplicate chunk. Ignore it and warn the sender to
                # stop sending chunks of the origin of the received
                # chunk "chunk_number".
                self.prune_origin(chunk_number, sender)
                
            else:
                
                # New chunk. chunk -> buffer[chunk_number]
                chunk = message[self.CHUNK]
                origin = message[self.ORIGIN]
                self.chunks[chunk_number % self.buffer_size] = (chunk, chunk_number, origin)
                self.received_chunks += 1

                if __debug__:
                    self.sender_of_chunks[chunk_number % self.buffer_size] = sender
                    chunks = ""
                    for n, c in self.chunks:
                        chunks += c
                        if c == "L":
                            self.sender_of_chunks[n % self.buffer_size] = ""
                            sim.FEEDBACK["DRAW"].put(("B", self.id, chunks,":".join(self.sender_of_chunks)))

                # When a peer X receives a chunk (number) C with origin Y,
                # for each peer P in forward[Y], X performs
                # pending[P].append(C).
                for P in self.forward[origin]:
                    pending[P].append(chunk_number)

                # When peer X receives a chunk, X selects the next
                # entry E of pending (one or more chunk numbers),
                # sends the chunk with chunk_number C indicated by
                # pending[E] to E, and removes C from pending[E]. If
                # in pending[E] there are more than one chunk
                # (number), all chunks are sent in a burst. E should
                # be selected to sent first to those peers that we
                # want to forward us chunks not originated in them.
                for C in self.pending[self.neighbor]:

                    # Send the chunk C to the neighbor.
                    self.send_chunk(C, self.neighbor)

                    # Increment the debt of the neighbor.
                    self.debt[self.neighbor] += 1

                    if self.debt[self.neighbor] > self.MAX_CHUNK_DEBT:

                        # Selfish neighbor detected: stop
                        # communicating with it.
                        lg.info("{}: removing {} by unsupportive ({} debts)".format(self.id, self.neighbor, self.debt[self.neighbor]))
                        del self.debt[self.neighbor]
                        for peer_list in self.forward:
                            if self.neighbor in peer_list:
                                peer_list.remove(self.neighbor)

                        if __debug__:
                            sim.FEEDBACK["DRAW"].put(("O", "Edge", "OUT", self.id, self.neighbor))

                # Select a different neighbor for the next chunk
                # reception.
                self.pending[(self.pending.index(self.neighbor) + 1) % len(self.pending)]

        else: # message[CHUNK_NUMBER] < 0

            if chunk_number == Common.REQUEST:

                lg.info("{}: received [request {}] from {}".format(self.id, chunk_number, sender))

                # If a peer X receives [request Y] from peer Z, X will
                # append Z to forward[Y.origin].

                origin = self.chunks[requested_chunk % self.BUFFER_SIZE][ORIGIN]
                
                if sender not in self.forward[origin]:

                    # Insert sender in the forwarding table.
                    self.forward[origin].append(sender)
                    lg.info("{}: chunks from {} will be sent to {}".format(self.id, origin, sender))

                    # Debt counter of sender.
                    self.debt[sender] = 0

                    if __debug__:
                        sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))
                        sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender))

            elif chunk_number == Common.PRUNE:
                
                chunk_number = message[1]
                lg.info("{}: received [prune {}] from {}".format(self.id, chunk_number, self.sender))

                origin = self.chunks[chunk_index % self.BUFFER_SIZE][self.ORIGIN]
                
                if sender in self.forward[origin]:
                    try:
                        self.forward[origin].remove(sender)
                    except ValueError:
                        lg.error("{}: failed to remove peer {} from forward table {} for origin {} ".format(self.id, sender, self.forward[origin], origin))
                    
            elif chunk_number == Common.HELLO:

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

                lg.info("{}: received [hello] from {}".format(self.id, sender))

                # If a peer X receives [hello] from peer Z, X will
                # append Z to forward[X].
        
                if sender not in self.forward[self.id]:

                    # Insert sender in the forward table.
                    self.forward[self.id].append(sender)
                    lg.info("{}: inserted {} in forward[{}] by [hello] from {}".format(self.id, sender, self.id, sender))

                    # Debt counter of sender.
                    self.debt[sender] = 0

                    if __debug__:
                        sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))
                        sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender))

            elif chunk_number == self.GOODBYE:

                lg.info("{}: received [goodbye] from {}".format(self.id, sender))

                if sender == self.splitter:
                    
                    lg.info("{}: received [goodbye] from splitter".format(self.id))
                    self.waiting_for_goodbye = False

                else:

                    for peers_list in self.forward:

                        if sender in peers_list:

                            try:
                                lg.info("{}: {} removing from {}".format(self.id, sender, peers_list))
                                peers_list.remove(sender)
                            except ValueError:
                                lg.error("{}: : failed to remove peer {} from {}".format(sef.id, sender, peers_list))
                                del self.debt[sender]

        return (chunk_number, sender)
        
    def process_next_message(self):
        msg, sender = self.team_socket.recvfrom(self.max_msg_length)
        if len(msg) == self.max_msg_length:
            message = struct.unpack("isi") # Chunk message [number, chunk, origin]
        elif len(msg) == struct.calcsize("ii"):
            message = struct.unpack("ii") # Control message [control, parameter]
        else:
            message = struct.unpack("i") # Control message [control]
        return self.process_message(message, sender)

    def buffer_data(self):
        for i in range(self.buffer_size):
            self.chunks.append((i, "L")) # L == Lost ??

        # Receive a chunk.
        (chunk_number, self.neighbor) = self.process_next_message()
        while(chunk_number < 0):
            (chunk_number,) = self.process_next_message()

        # The first chunk to play is the firstly received chunk.
        self.played_chunk = chunk_number

        lg.info("{}: position in the buffer of the first chunk to play".format(self.id, self.played_chunk))
        
        while (chunk_number < self.played_chunk) or (((chunk_number - self.played_chunk) % self.buffer_size) < (self.buffer_size // 2)):
            (chunk_number,) = self.process_next_message()
            while (chunk_number < self.played_chunk):
                (chunk_number,) = self.process_next_message()
        self.prev_received_chunk = chunk_number

    def request_chunks(self, chunk_number, peer):
        msg = struct.pack("ii", self.REQUEST, chunk_number)
        self.team_socket.sendto(msg, peer)
        lg.info("{}: [request {}] sent to {}".format(self.id, chunk_number, peer))

    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number % self.buffer_size][CHUNK_NUMBER] == "C":
            self.played += 1
        else:
            self.losses += 1
            lg.info("{}: lost chunk! {}".format(self.id, chunk_number))

            # The chunk "chunk_number" has not been received on time
            # and it is quite probable that is not going to change in
            # the near future. The action here is to request the lost
            # chunk to one or more peers using a [request
            # <chunk_number>]. If after this, I will start receiving
            # duplicate chunks, then a [prune <chunk_number>] should
            # be sent to those peers which send duplicates.
            self.request_chunk(chunk_number, self.neighbor)
            # Here, self.neighbor has been selected by
            # simplicity. However, other alternatives such as
            # requesting the lost chunk to the neighbor with smaller
            # debt could also be explored.
            
        self.number_of_chunks_consumed += 1
        return self.player_alive

    def play_next_chunks(self, last_received_chunk):
        for i in range(last_received_chunk - self.prev_received_chunk):
            self.player_alive = self.play_chunk(self.played_chunk)
            self.chunks[self.played_chunk % self.buffer_size] = (self.played_chunk, "L")
            self.played_chunk = (self.played_chunk + 1) % Common.MAX_CHUNK_NUMBER
        if ((self.prev_received_chunk % Common.MAX_CHUNK_NUMBER) < last_received_chunk):
            self.prev_received_chunk = last_received_chunk

    def keep_the_buffer_full(self):
        (last_received_chunk, ) = self.process_next_message()
        while (last_received_chunk < 0):
            (last_received_chunk, ) = self.process_next_message()

        self.play_next_chunks(last_received_chunk)

    def start(self):
        Thread(target=self.run).start()

    def say_goodbye_to_the_team(self):
        for peer in self.peer_list:
            self.say_goodbye(peer)

        while (all(len(d) > 0 for d in self.pending)):
            self.process_next_message()

        self.ready_to_leave_the_team = True
        lg.info("{}: see you later!".format(self.id))

    def run(self):
        self.buffer_data()
        while (self.player_alive or self.waiting_for_goodbye):
            self.keep_the_buffer_full()
            if not self.player_alive:
                self.say_goodbye(self.splitter)
        self.say_goodbye_to_the_team()
        self.team_socket.close()

    def am_i_a_monitor(self):
        return self.number_of_peers < self.number_of_monitors

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
