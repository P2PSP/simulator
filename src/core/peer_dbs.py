"""
@package simulator
peer_dbs module
"""

# Abstract class

# DBS (Data Broadcasting Set) layer, peer side. Full-connected overlay.

# DBS peers receive chunks from the splitter and other peers, and
# resend them to the rest of peers of the team.

import random
import sys

import logging
import struct
import time
from threading import Thread
#import netifaces
from .messages import Messages
from .limits import Limits
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .ip_tools import IP_tools
from .chunk_structure import ChunkStructure

class Peer_DBS():

    peer_port = 4553
    splitter = ("localhost", 4552)

    def __init__(self, id, name, loglevel):

        self.lg = logging.getLogger(name)
        self.lg.setLevel(loglevel)
        self.public_endpoint = (None, 0)
        self.chunk_to_play = 0
        self.buffer = []
        self.player_connected = True
        self.waiting_for_goodbye = True
        self.ready_to_leave_the_team = False

        # The chunks received from the splitter (originated at this
        # peer) will be forwarded to all the peers pointed by this
        # dictionary that has only one entry (the public endpoint of
        # the peer).
        self.forward = {}

        # List of pending chunks (numbers) to be sent to peers. Por
        # example, if pending[X] = [1,5,7], the chunks stored in
        # entries 1, 5, and 7 of the buffer will be sent to the peer
        # X, in a burst, when a chunk arrives. The number of entries
        # (keys) in pending{} is the fan-out of the peer. This fan-out
        # matches the number of different destinations that there are
        # in forward.
        self.pending = {}

        self.sendto_counter = 0
        self.received_chunks = 0

        self.chunk_packet_format = "!isIi"
        #                           |||||
        #                           ||||+-- Chunk data
        #                           |||+--- Port
        #                           ||+---- IP address
        #                           |+----- Chunk number
        #                           +------ Network endian

        self.max_packet_length = struct.calcsize(self.chunk_packet_format)
        self.neighbor_index = 0 
        self.number_of_chunks_consumed = 0 # Simulation ?
        self.number_of_lost_chunks = 0 # Simulation?
        self.played = 0 # Simulation?
        self.rounds_counter = 0 # Simulation?
        self.activity = {}  # Incremented if received a chunk in the last round from that origin
        self.prev_chunk_number_round = 0 # Simulator?
        self.name = name
        self.lg.info(f"{name} {self.public_endpoint}: DBS initialized")

    def set_splitter(self, splitter):
        self.splitter = splitter

    def listen_to_the_team(self):
        self.team_socket = socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, loglevel=self.lg.level)
        self.team_socket.bind(self.public_endpoint)
        self.lg.info(f"{self.ext_id}: listening to the team")
        self.say_hello(self.splitter)  # Only works for cone NATs
        #self.team_socket.bind(("", self.public_endpoint[1]))
        #self.team_socket.settimeout(self.timeout) # In seconds
        #self.team_socket.setblocking(0)

    def receive_public_endpoint(self):
        msg_length = struct.calcsize("!Ii")
        msg = self.splitter_socket.recv(msg_length)
        pe = struct.unpack("!Ii", msg)
        self.public_endpoint = (IP_tools.int2ip(pe[0]), pe[1])
        self.lg.info(f"{self.public_endpoint}: received public_endpoint")
        self.ext_id = ("%03d" % self.peer_index_in_team, self.public_endpoint[0], int("%5d" % self.public_endpoint[1]))
        self.lg.info(f"{self.ext_id}: peer_index_in_team={self.peer_index_in_team}")

    def receive_buffer_size(self):
        msg_length = struct.calcsize("!H")
        msg = self.splitter_socket.recv(msg_length)
        self.buffer_size = struct.unpack("!H", msg)[0]
        self.lg.info(f"{self.ext_id}: buffer_size={self.buffer_size}")
        
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
            
            # I'll forward at least the chunks received from the splitter.
            self.forward[self.public_endpoint].append(peer)
            self.pending[peer] = []
            
            self.say_hello(peer)
            #self.debts[peer] = 0
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
        #self.private_endpoint = self.splitter_socket.getsockname()
        #print("{}: I'm a peer".format(self.id))
        self.lg.info(f"{self.public_endpoint}: I am a peer")
        #self.neighbor = self.id
        #print("self.neighbor={}".format(self.neighbor))
        #self.pending[self.id] = []

        #print("{}: connected to the splitter at {}".format(self.id, self.splitter))
        self.lg.info(f"{self.public_endpoint}: connected to the splitter at {self.splitter}")

    def buffer_chunk(self, chunk_number, origin, chunk_data, sender):
        position = chunk_number % self.buffer_size
        self.lg.info(f"{self.ext_id}: buffer_chunk: buffering ({chunk_number}, {chunk_data}, {origin}) sent by {sender} in position {position}")
        self.buffer[chunk_number % self.buffer_size] = (chunk_number, chunk_data, origin)

        if sender == self.splitter:

            self.update_pendings(origin, chunk_number)

            #if self.ext_id[0] == '000': #!
            #    sys.stderr.write(f" {[i for i in self.activity.values()]}") #!

            for origin in list(self.activity):
                if self.activity[origin] < -5:
                    del self.activity[origin]
                    for neighbors in self.forward.values():
                        if origin in neighbors:
                            neighbors.remove(origin)

            for origin in self.activity.keys():
                self.activity[origin] -= 1

            # New round, all pending chunks are sent
            self.lg.info(f"{self.ext_id}: buffer_chunk: flushing chunks to {len(self.pending)} neighbors={self.pending.keys()}")
            for neighbor in self.pending:
                self.lg.info(f"{self.ext_id}: buffer_chunk: flushing {len(self.pending[neighbor])} chunks to neighbor {neighbor}")
                self.send_chunks(neighbor)

            # Delete the sent chunks of pending
            #for neighbor in self.pending:
            #    del self.pending[neighbor][:]  # Delete the content of the list, but no the pointer to the list

            # Simulator?
            if __debug__:
                self.rounds_counter += 1
                for origin, neighbors in self.forward.items():
                    buf = ''
                    #for i in neighbors:
                    #    buf += str(i)
                    buf = len(neighbors)*"#"
                    #self.lg.info(f"{self.ext_id}: round={self.rounds_counter:03} origin={origin} K={len(neighbors):02} fan-out={buf:10}")
                    self.lg.debug(f"{self.ext_id}: buffer_chunk: BUFFER={self.buffer}")
                try:
                    CLR = self.number_of_lost_chunks / (chunk_number - self.prev_chunk_number_round)
                    self.lg.info(f"{self.ext_id}: CLR={CLR:1.3} losses={self.number_of_lost_chunks} chunk_number={chunk_number} increment={chunk_number - self.prev_chunk_number_round}")
                except ZeroDivisionError:
                    pass
                self.prev_chunk_number_round = chunk_number

            self.number_of_lost_chunks = 0 # ?? Simulator

        else:

            # Chunk received from a peer
            try:
                self.activity[origin] += 1
            except KeyError:
                self.activity[origin] = 1

        # For all received chunks

        # Select next entry in pending with chunks to send
        if len(self.pending) > 0:
            counter = 0
            neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
            self.send_chunks(neighbor)
            while len(self.pending[neighbor]) == 0:
                self.neighbor_index = list(self.pending.keys()).index(neighbor) + 1
                neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
                counter += 1
                if counter > len(self.pending):
                    break

    def update_pendings(self, origin, chunk_number):
        # A new chunk has been received, and this chunk has an origin
        # (not necessarily the sender of the chunk). For all peers P_i in
        # forward[origin] the chunk (number) is appended to pending[P_i].

        for peer in self.forward[origin]:
            try:
                self.pending[peer].append(chunk_number)
            except KeyError:
                self.pending[peer] = [chunk_number]

    def compose_message(self, chunk_number):
        chunk_position = chunk_number % self.buffer_size
        chunk = self.buffer[chunk_position]
        stored_chunk_number = chunk[ChunkStructure.CHUNK_NUMBER]
        chunk_data = chunk[ChunkStructure.CHUNK_DATA]
        chunk_origin_IP = chunk[ChunkStructure.ORIGIN][0]
        chunk_origin_port = chunk[ChunkStructure.ORIGIN][1]
        content = (stored_chunk_number, chunk_data, IP_tools.ip2int(chunk_origin_IP), chunk_origin_port)
        self.lg.info(f"{self.ext_id}: compose_message: chunk_position={chunk_position} chunk_number={self.buffer[chunk_position][ChunkStructure.CHUNK_NUMBER]} origin={self.buffer[chunk_position][ChunkStructure.ORIGIN]}")
        packet = struct.pack(self.chunk_packet_format, *content)
        return packet

    def send_chunk_to_peer(self, chunk_number, destination):
        #if (self.ext_id[0] == '001') or (self.ext_id[0] == '002'): #!
        #if (self.ext_id[0] == '001') : #!
        #    prob = random.random()  #!
        #    if prob >= 2:         #!
        #        return              #!
        self.lg.info(f"{self.ext_id}: send_chunk_to_peer: chunk {chunk_number} sent to {destination}")
        msg = self.compose_message(chunk_number)
        #msg = struct.pack("isIi", stored_chunk_number, chunk_data, socket.ip2int(chunk_origin_IP), chunk_origin_port)
        self.team_socket.sendto(msg, destination)
        self.sendto_counter += 1
            #self.lg.debug("{}: sent chunk {} (with origin {}) to {}".format(self.ext_id, chunk_number, (chunk_origin_IP, chunk_origin_port), peer))
        #except TypeError:
        #    self.lg.warning(f"{self.ext_id}: chunk {chunk_number} not sent because it was lost")
        #    pass

    def process_hello(self, sender):

        self.lg.debug("{}: received [hello] from {}".format(self.ext_id, sender))

        # If a peer X receives [hello] from peer Z, X will
        # append Z to forward[X].

        if sender not in self.forward[self.public_endpoint]:
            self.forward[self.public_endpoint].append(sender)
            self.pending[sender] = []
            self.provide_hello_feedback(sender)

    def process_goodbye(self, sender):
        self.lg.info(f"{self.ext_id}: process_goodbye: received [goodbye] from {sender}")

        if sender == self.splitter:
            self.waiting_for_goodbye = False
            self.player_connected = False
        else:
            for peers_list in self.forward.values():
                self.lg.info(f"{self.ext_id}: process_goodbye: {sender} removing from {peers_list}")
                try:
                    peers_list.remove(sender)
                except ValueError:
                    self.lg.warning(f"{self.ext_id}: process_goodbye: failed to remove peer {sender} from {peers_list}")
            
    def process_unpacked_message(self, message, sender):

        chunk_number = message[ChunkStructure.CHUNK_NUMBER]

        if chunk_number >= 0:

            # We have received a chunk.
            chunk_data = message[ChunkStructure.CHUNK_DATA]
            origin = message[ChunkStructure.ORIGIN]
            chunk_data = message[ChunkStructure.CHUNK_DATA]
            self.received_chunks += 1
            self.provide_CLR_feedback(sender)
            self.buffer_chunk(chunk_number = chunk_number, origin = origin, chunk_data = chunk_data, sender = sender)

        else:  # message[ChunkStructure.CHUNK_NUMBER] < 0

            if chunk_number == Messages.HELLO:
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

        self.lg.info(f"{self.ext_id}: send_chunks: (begin) neighbor={neighbor} pending[{neighbor}]={self.pending[neighbor]}")
        while self.pending[neighbor]:
            chunk_number = self.pending[neighbor].pop(0)
            self.lg.info(f"{self.ext_id}: send_chunks: sending chunk_number={chunk_number} to neighbor={neighbor}")
           
            if __debug__:
                if neighbor == self.public_endpoint:
                    self.lg.error(f"{self.ext_id}: send_chunks: sending a chunk {chunk_number} to myself={neighbor} forward={self.forward}")

            self.send_chunk_to_peer(chunk_number, neighbor)
        self.lg.info(f"{self.ext_id}: send_chunks: (end) neighbor={neighbor} pending[{neighbor}]={self.pending[neighbor]}")

    def receive_packet(self):

        return self.team_socket.recvfrom(self.max_packet_length)

    def process_next_message(self):

        packet, sender = self.receive_packet()
        return self.unpack_message(packet, sender)

    def unpack_message(self, packet, sender):

        if len(packet) == self.max_packet_length:
            message = struct.unpack(self.chunk_packet_format, packet)
            message = message[ChunkStructure.CHUNK_NUMBER], \
                message[ChunkStructure.CHUNK_DATA], \
                (IP_tools.int2ip(message[ChunkStructure.ORIGIN]), message[ChunkStructure.ORIGIN+1])

        elif len(packet) == struct.calcsize("!iii"):
            message = struct.unpack("!iii", packet)  # Control message: [control, parameter, parameter]
        elif len(packet) == struct.calcsize("!ii"):
            message = struct.unpack("!ii", packet)  # Control message: [control, parameter]
        else:
            message = struct.unpack("!i", packet)  # Control message: [control]
        x = self.process_unpacked_message(message, sender)
        return x

    # Only monitors complain
#    def complain(self, chunk_number):
#        pass

    def play_chunk(self, chunk_number):
        buffer_box = self.buffer[chunk_number % self.buffer_size]
        if buffer_box[ChunkStructure.CHUNK_DATA] != b'L':
            # Only the data will be empty in order to remember things ...
            clear_entry_in_buffer = (buffer_box[ChunkStructure.CHUNK_NUMBER], b'L', buffer_box[ChunkStructure.ORIGIN])
#            self.buffer[chunk_number % self.buffer_size] = (-1, b'L', None)
            self.buffer[chunk_number % self.buffer_size] = clear_entry_in_buffer
            self.played += 1
        else:
            # The cell in the buffer is empty.
            self.complain(chunk_number) # Only monitors
            self.number_of_lost_chunks += 1
            self.lg.warning(f"{self.ext_id}: play_chunk: lost chunk! {self.chunk_to_play} (number_of_lost_chunks={self.number_of_lost_chunks})")

        self.number_of_chunks_consumed += 1

        if __debug__:
            # Showing buffer
            buf = ""
            for i in self.buffer:
                if i[ChunkStructure.CHUNK_DATA] != b'L':
                    try:
                        _origin = list(self.forward[self.public_endpoint]).index(i[ChunkStructure.ORIGIN])
                        buf += hash(_origin)
                    except ValueError:
                        buf += '-' # Peers do not exist in their team.
                else:
                    buf += " "
            self.lg.debug(f"{self.ext_id}: play_chunk: buffer={buf}")

    def play_next_chunks(self, last_received_chunk):
        for i in range(last_received_chunk - self.prev_received_chunk):
            #self.player_connected = self.play_chunk(self.chunk_to_play)
            self.play_chunk(self.chunk_to_play)
            #self.buffer[self.chunk_to_play % self.buffer_size] = (-1, b'L', None)
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

        self.play_next_chunks(last_received_chunk)

    # To be placed in peer_dbs_sim ?
    def compose_goodbye_message(self):
        msg = struct.pack("!i", Messages.GOODBYE)
        return msg

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

        # The first chunk to play is the firstly received chunk (which
        # probably will not be the received chunk with the smallest
        # index).
        self.chunk_to_play = chunk_number

        self.lg.info(f"{self.ext_id}: buffer_data: position in the buffer of the first chunk to play={self.chunk_to_play}")

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
        self.lg.info(f"{self.ext_id}: waiting for the chunks ...")

        for i in range(self.buffer_size):
            self.buffer.append((-1, b'L', None, 0))  # L == Lost

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
        self.lg.info(f"{self.ext_id}: run: player_connected={self.player_connected} waiting_for_goodbye={self.waiting_for_goodbye}")
        for i in range(10):
            self.say_goodbye(self.splitter)
            self.lg.info(f"{self.ext_id}: sent [goodbye] to the splitter {self.splitter}")
        self.say_goodbye_to_the_team()

        # Send pending chunks
        for peer, chunks in self.pending.items():
            for chunk in chunks:
                self.send_chunk_to_peer(chunk, peer)

        # Print some statistics <--------- Simulator?
        total_lengths = 0
        #max_length = 0
        entries = 0
        for origin, peers_list in self.forward.items():
            self.lg.debug(f"{self.ext_id}: goodbye forward[{origin}]={peers_list} {len(peers_list)}")
            total_lengths += len(peers_list)
            if(len(peers_list) > 0):  # This should not be necessary
                entries += 1
        try:
            avg = total_lengths/entries
        except:
            avg = 0
        self.lg.info(f"{self.ext_id}: average_neighborhood_degree={avg} ({total_lengths}/{entries})") # Wrong!!!!!!!!!!!!!!!!!!!!!

        self.lg.debug(f"{self.ext_id}: forward = {self.forward}")
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
