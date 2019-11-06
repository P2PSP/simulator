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

import time
import struct
from threading import Thread
#import netifaces
from .messages import Messages
from .limits import Limits
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .ip_tools import IP_tools
from .chunk_structure import ChunkStructure
import logging
import core.stderr as stderr

class Peer_DBS():

    #peer_port = 4553
    #splitter = ("localhost", 4552)

    def __init__(self):
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
        self.set_packet_format()
        self.max_packet_length = struct.calcsize(self.packet_format)
        self.neighbor_index = 0 
        self.number_of_chunks_consumed = 0 # Simulation ?
        self.number_of_lost_chunks_in_this_round = 0 # Simulation?
        self.played = 0 # Simulation?
        self.rounds_counter = 0 # Simulation?
        self.activity = {}  # Incremented if received a chunk in the last round from that origin
        self.prev_chunk_number_received_from_the_splitter = 0 # Simulator?
        #self.delta = 0
        #self.delta_inertia = {}

        logging.basicConfig(stream=sys.stdout, format="%(asctime)s.%(msecs)03d %(message)s %(levelname)-8s %(name)s %(pathname)s:%(lineno)d", datefmt="%H:%M:%S")
        self.lg = logging.getLogger(__name__)
        if __debug__:
            self.lg.setLevel(logging.DEBUG)
        else:
            self.lg.setLevel(logging.ERROR)

    def set_splitter(self, splitter):
        self.splitter = splitter

    def set_min_activity(self, min_activity):
        self.min_activity = min_activity

    def listen_to_the_team(self):
        self.team_socket = socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.team_socket.bind(self.public_endpoint)
        #self.team_socket.bind((IP_tools.int2ip(self.public_endpoint[0]), self.public_endpoint[1]))
        self.say_hello(self.splitter)  # Only works for cone NATs
        #self.team_socket.bind(("", self.public_endpoint[1]))
        #self.team_socket.settimeout(self.timeout) # In seconds
        #self.team_socket.setblocking(0)
        self.lg.debug(f"{self.ext_id}: listening to the team")

    def receive_the_public_endpoint(self):
        msg_length = struct.calcsize("!Ii")
        msg = self.splitter_socket.recv(msg_length)
        pe = struct.unpack("!Ii", msg)
        self.public_endpoint = (IP_tools.int2ip(pe[0]), pe[1])
        #self.public_endpoint = pe[0], pe[1]
        #self.public_endpoint = struct.unpack("!Ii", msg)
        self.lg.debug(f"{self.public_endpoint}: received public_endpoint")

    def receive_the_buffer_size(self):
        msg_length = struct.calcsize("!H")
        msg = self.splitter_socket.recv(msg_length)
        self.buffer_size = struct.unpack("!H", msg)[0]
        self.lg.debug(f"{self.ext_id}: buffer_size={self.buffer_size}")

    def receive_the_number_of_peers(self):
        msg_length = struct.calcsize("!H")
        msg = self.splitter_socket.recv(msg_length)
        self.number_of_peers = struct.unpack("!H", msg)[0]
        self.lg.debug(f"{self.ext_id}: number_of_peers={self.number_of_peers}")

    def receive_the_peer_index_in_team(self):
        msg_length = struct.calcsize("!H")
        msg = self.splitter_socket.recv(msg_length)
        self.peer_index_in_team = struct.unpack("!H", msg)[0]
        self.ext_id = ("%03d" % self.peer_index_in_team, self.public_endpoint[0], int("%5d" % self.public_endpoint[1]))
        self.lg.debug(f"{self.ext_id}: peer_index_in_team={self.peer_index_in_team}")

    def send_ready_for_receiving_chunks(self):
        # self.splitter_socket.send(b"R", "s") # R = Ready
        msg = struct.pack("s", b"R")
        self.splitter_socket.send(msg)
        self.lg.debug(f"{self.ext_id}: sent [ready] to the splitter")

    def say_hello(self, entity):
        msg = struct.pack("!i", Messages.HELLO)
        self.team_socket.sendto(msg, entity)
        self.lg.debug(f"{self.ext_id}: sent [hello] to {entity}")

    def receive_the_list_of_peers(self):
        self.lg.debug(f"{self.ext_id}: receiving the list of peers")
        peers_pending_of_reception = self.number_of_peers
        msg_length = struct.calcsize("!Ii")
        counter = 0

        # Peer self.id will forward by default all chunks received
        # from the splitter (originated at itself).
        self.forward[self.public_endpoint] = []

        while peers_pending_of_reception > 0:
            msg = self.splitter_socket.recv(msg_length)
            neighbor = struct.unpack("!Ii", msg)
            neighbor = (IP_tools.int2ip(neighbor[0]), neighbor[1])
            
            # I'll forward at least the chunks received from the splitter.
            self.forward[self.public_endpoint].append(neighbor)
            self.pending[neighbor] = []

            #self.delta_inertia[neighbor] = 0.0
            
            self.say_hello(neighbor)
            self.lg.debug(f"{self.ext_id}: peer {neighbor} is in the team")
            counter += 1
            peers_pending_of_reception -= 1

        self.lg.debug(f"{self.ext_id}: forward={self.forward}")
        self.lg.debug(f"{self.ext_id}: pending={self.pending}")

    def connect_to_the_splitter(self, peer_port):
        self.lg.debug(f"{self.public_endpoint}: connecting to the splitter at {self.splitter}")
        host_name = socket.gethostname()
        for i in range(3):
            while True:
                try:
                    address = socket.gethostbyname(host_name)
                except socket.gaierror:
                    continue
                break
        self.splitter_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.splitter_socket.set_id(self.id) # Ojo, simulation dependant
        #host = socket.gethostbyname(socket.gethostname())
        #iface = netifaces.interfaces()[8]      # Name of the second interface
        #stuff = netifaces.ifaddresses(iface)   # Configuration data
        #stderr.write(f"---------------> {stuff}")
        #time.sleep(1000)
        #IP_stuff = stuff[netifaces.AF_INET][0] # Only the IP stuff
        #address = IP_stuff['addr']             # Get local IP addr
        self.splitter_socket.bind((address, peer_port))

        try:
            self.splitter_socket.connect(self.splitter)
        except ConnectionRefusedError as error:
            stderr.write(f"{self.public_endpoint}: {error} when connecting to the splitter {self.splitter}")
            return False
        except ConnectionResetError as error:
            stderr.write(f"{self.public_endpoint}: {error} when connecting to the splitter {self.splitter}")
            return False

        # The index for pending[].
        self.splitter = self.splitter_socket.getpeername() # Be careful, not "127.0.1.1 hostname" in /etc/hosts
        #self.private_endpoint = self.splitter_socket.getsockname()
        self.lg.debug(f"{self.public_endpoint}: connected to the splitter at {self.splitter}")
        return True

    def send_chunks(self, neighbor):
        assert len(self.pending[neighbor]) > 0, f"{len(self.pending[neighbor])}"
        self.lg.debug(f"{self.ext_id}: sending chunks {self.pending[neighbor]} {len(self.pending[neighbor])} to neighbor={neighbor}")
        # When peer X receives a chunk, X selects the next
        # entry pending[E] (with one or more chunk numbers),
        # sends the chunk with chunk_number C indicated by
        # pending[E] to E, and removes C from pending[E]. If
        # in pending[E] there are more than one chunk
        # (number), all chunks are sent in a burst. E should
        # be selected to sent first to those peers that we
        # want to forward us chunks not originated in them.
        while self.pending[neighbor]:
            chunk_number = self.pending[neighbor].pop(0)
            self.send_chunk_to_peer(chunk_number, neighbor)
        assert len(self.pending[neighbor]) == 0, f"len(self.pending[{neighbor}])={len(self.pending[neighbor])}"

    def send_chunk_to_peer(self, chunk_number, destination):
        packet = self.create_packet(chunk_number)
        self.team_socket.sendto(packet, destination)
        self.sendto_counter += 1
        self.lg.debug(f"{self.ext_id}: chunk {chunk_number} sent to {destination}")
        try:
            self.activity[destination] -= 1
        except KeyError:
            self.activity[destination] = 0
            
        #if self.activity[destination] < self.min_activity:
        #    del self.activity[destination]
        #    for destinations_list in self.forward.values():
        #        if destination in destinations_list:
        #            destinations_list.remove(destination)
        #            self.lg.debug(f"{self.ext_id}: removed {destination}")
        #        assert destination not in destinations_list, f"{self.ext_id}: {destination} still in {self.forward}"
        #    self.lg.debug(f"{self.ext_id}: forward={self.forward}")
        #self.lg.debug(f"{self.ext_id}: activity={self.activity}")

    def send_chunks_to_the_next_neighbor(self):
        self.lg.debug(f"{self.ext_id}: sending chunks to neighbors (pending={self.pending} forward={self.forward})")
        # Select next entry in pending with chunks to send
        if len(self.pending) > 0:
            counter = 0
            neighbor = list(self.pending.keys())[self.neighbor_index]
            self.lg.debug(f"{self.ext_id}: selected neighbor {neighbor} from {self.pending.keys()}")
            if len(self.pending[neighbor])>0:
                assert len(self.pending[neighbor]) > 0, f"{len(self.pending[neighbor])}"
                self.send_chunks(neighbor)
            assert len(self.pending[neighbor]) == 0, \
                f"{self.ext_id}: {self.pending}"
            while len(self.pending[neighbor]) == 0:
                self.neighbor_index = (list(self.pending.keys()).index(neighbor) + 1) % len(self.pending)
                neighbor = list(self.pending.keys())[self.neighbor_index]
                if counter > len(self.pending):
                    break
                counter += 1

    def buffer_chunk(self, chunk):
        position = chunk[ChunkStructure.CHUNK_NUMBER] % self.buffer_size
        self.buffer[position] = chunk
        self.lg.debug(f"{self.ext_id}: buffering chunk={chunk} buffer={self.buffer}")

    def update_pendings(self, origin, chunk_number):
        self.lg.debug(f"{self.ext_id}: updating pendings (origin={origin}, chunk_number={chunk_number})")
        assert origin in self.forward, f"{self.ext_id}: {origin} is not in the forwarding table={self.forward}"
        for neighbor in self.forward[origin]:
            try:
                self.pending[neighbor].append(chunk_number)
            except KeyError:
                self.pending[neighbor] = [chunk_number]

    def on_chunk_received_from_the_splitter(self, chunk):
        chunk_number = chunk[ChunkStructure.CHUNK_NUMBER]
        if __debug__:
            origin = chunk[ChunkStructure.ORIGIN_ADDR], chunk[ChunkStructure.ORIGIN_PORT]
            self.lg.debug(f"{self.ext_id}: processing chunk {chunk_number} with origin {origin} received from the splitter")

        # A new chunk is received from the splitter, so, a new chunk
        # must be forwarded to the rest of the team.
        #for neighbor in self.forward[self.public_endpoint]:
        #    try:
        #        self.pending[neighbor].append(chunk_number)
        #    except KeyError:
        #        self.pending[neighbor] = [chunk_number]
        self.update_pendings(self.public_endpoint, chunk_number)

        # Increase inactivity and remove selfish neighbors.
        #for neighbor in list(self.activity.keys()):
        #    self.activity[neighbor] -= 1
        ##for neighbor in list(self.activity):    
        #    if self.activity[neighbor] < self.min_activity:
        #        del self.activity[neighbor]
        #        for neighbors_list in self.forward.values():
        #            if neighbor in neighbors_list:
        #                neighbors_list.remove(neighbor)

        # New round, all pending chunks are sent for neighbor in self.pending:
        # self.send_chunks(neighbor)

        if __debug__:
            self.rounds_counter += 1
            for origin, neighbors in self.forward.items():
                buf = ''
                #for i in neighbors:
                #    buf += str(i)
                buf = len(neighbors)*"#"
                self.lg.debug(f"{self.ext_id}: round={self.rounds_counter:03} origin={origin} K={len(neighbors):02} fan-out={buf:10}")

            try:
                CLR = self.number_of_lost_chunks_in_this_round / (chunk_number - self.prev_chunk_number_received_from_the_splitter)
                self.lg.debug(f"{self.ext_id}: CLR={CLR:1.3} losses={self.number_of_lost_chunks_in_this_round} chunk_number={chunk_number} increment={chunk_number - self.prev_chunk_number_received_from_the_splitter}")
            except ZeroDivisionError:
                pass
            self.prev_chunk_number_received_from_the_splitter = chunk_number
            self.number_of_lost_chunks_in_this_round = 0

    def compute_deltas(self, chunk_number, sender):
        #self.delta = chunk_number - self.delta
        delta = chunk_number - self.chunk_to_play
        try:
            self.delta_inertia[sender] = abs(delta)*0.1 + self.delta_inertia[sender]*0.9
        except KeyError:
            self.delta_inertia[sender] = 0.0
        #self.delta = chunk_number
        self.lg.debug(f"{self.ext_id}: inertia {self.delta_inertia}")

    def on_chunk_received_from_a_peer(self, chunk, sender):
        # Extend the list of known peers checking if the origin of
        # the received chunk is new. DBS specific because peers
        # will forward to the <origin> all chunks originated at
        # themselves (received by the splitter).
        chunk_number = chunk[ChunkStructure.CHUNK_NUMBER]
        origin = chunk[ChunkStructure.ORIGIN_ADDR], chunk[ChunkStructure.ORIGIN_PORT]
        self.lg.debug(f"{self.ext_id}: processing chunk {chunk_number} with origin {origin}")

        if origin not in self.forward[self.public_endpoint]:
            self.forward[self.public_endpoint].append(origin)

        try:
            self.activity[sender] += 1
        except KeyError:
            self.activity[sender] = 1

        #self.compute_deltas(chunk_number, origin)

    def process_chunk(self, chunk, sender):
        self.lg.debug(f"{self.ext_id}: processing chunk={chunk}")
        self.buffer_chunk(chunk)
        if sender == self.splitter:
            self.on_chunk_received_from_the_splitter(chunk)
        else:
            self.on_chunk_received_from_a_peer(chunk, sender)

    def process_hello(self, sender):
        self.lg.debug(f"{self.ext_id}: received [hello] from {sender}")
        # If a peer X receives [hello] from peer Z, X will
        # append Z to forward[X].
        if sender not in self.forward[self.public_endpoint]:
            self.forward[self.public_endpoint].append(sender)
            self.pending[sender] = []
        #self.delta_inertia[sender] = 0.0

    def process_goodbye(self, sender):
        self.lg.debug(f"{self.ext_id}: received [goodbye] from {sender}")
        if sender == self.splitter:
            self.waiting_for_goodbye = False
            self.player_connected = False
        else:
            for peers_list in self.forward.values():
                try:
                    peers_list.remove(sender)
                except ValueError:
                    stderr.write(f"{self.ext_id}: failed to remove peer {sender} from {peers_list}")

    def receive_packet(self):
        return self.team_socket.recvfrom(self.max_packet_length)

    def process_next_message(self):
        packet, sender = self.receive_packet()
        return self.unpack_message(packet, sender)

    def create_packet(self, chunk_number):
        chunk_position = chunk_number % self.buffer_size
        chunk = self.buffer[chunk_position].copy()
        assert len(chunk)==len(self.packet_format)-1, f"{chunk} {len(chunk)} {self.packet_format}"
        chunk[ChunkStructure.ORIGIN_ADDR] = IP_tools.ip2int(chunk[ChunkStructure.ORIGIN_ADDR])
        packet = struct.pack(self.packet_format, *chunk)
        return packet

    def ___unpack_message(self, packet, sender):
        if len(packet) == self.max_packet_length:
            message = self.unpack_chunk(packet)
        elif len(packet) == struct.calcsize("!iIi"):
            message = struct.unpack("!iIi", packet)  # Control message: [control, parameter, parameter]
        elif len(packet) == struct.calcsize("!ii"):
            message = struct.unpack("!ii", packet)  # Control message: [control, parameter]
        else:
            message = struct.unpack("!i", packet)  # Control message: [control]
        x = self.process_unpacked_message(message, sender)
        return x

    def complain(self, chunk_number):
        # Only monitors complain
        pass

    def play_chunk(self, chunk_number):
        buffer_box = self.buffer[chunk_number % self.buffer_size]
        self.lg.debug(f"{self.ext_id}: chunk={chunk_number} hops={buffer_box[ChunkStructure.HOPS]}")
        if buffer_box[ChunkStructure.CHUNK_DATA] != b'L':
            # Only the chunk data is deleted.
            self.buffer[chunk_number % self.buffer_size] = self.clear_entry_in_buffer(buffer_box)
            self.played += 1
        else:
            # The cell in the buffer is empty.
            self.complain(chunk_number) # Only monitors
            self.number_of_lost_chunks_in_this_round += 1
            self.lg.debug(f"{self.ext_id}: lost chunk! {self.chunk_to_play} (number_of_lost_chunks={self.number_of_lost_chunks_in_this_round})")

        self.number_of_chunks_consumed += 1
        if __debug__:
            buf = ""
            for i in self.buffer:
                if i[ChunkStructure.CHUNK_DATA] != b'L':
                    try:
                        _origin = list(self.forward[self.public_endpoint]).index((i[ChunkStructure.ORIGIN_ADDR],i[ChunkStructure.ORIGIN_PORT]))
                        buf += hash(_origin)
                    except ValueError:
                        buf += '-' # Peers do not exist in their forwarding table.
                else:
                    buf += " "
            self.lg.debug(f"{self.ext_id}: buffer={buf}")        

    def play_next_chunks(self, last_received_chunk):
        for i in range(last_received_chunk - self.prev_received_chunk):
            #self.player_connected = self.play_chunk(self.chunk_to_play)
            self.play_chunk(self.chunk_to_play)
            #self.buffer[self.chunk_to_play % self.buffer_size] = (-1, b'L', None, 0)
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

    def compose_goodbye_message(self):
        msg = struct.pack("!i", Messages.GOODBYE)
        return msg

    def say_goodbye(self, peer):
        # self.team_socket.sendto(Messages.GOODBYE, "i", peer)
        msg = self.compose_goodbye_message()
        self.team_socket.sendto(msg, peer)
        self.lg.debug(f"{self.ext_id}: sent [goodbye] to the team")

    def say_goodbye_to_the_team(self):
        for origin, peer_list in self.forward.items():
            for peer in peer_list:
                self.say_goodbye(peer)

        # Next commented lines freeze the peer (in a receive() call)
        # while (all(len(d) > 0 for d in self.pending)):
        #     self.process_next_message()

        self.ready_to_leave_the_team = True

    def buffer_data(self):
        if __debug__:
            self.lg.debug(f"{self.ext_id}: buffering")
            start_time = time.time()
        
        # Receive a chunk.
        (chunk_number, sender) = self.process_next_message()
        self.prev_received_chunk = chunk_number # <-----
        self.delta = chunk_number
        while (chunk_number < 0):
            (chunk_number, sender) = self.process_next_message()
            if self.player_connected == False:
                break

        # The first chunk to play is the firstly received chunk (which
        # probably will not be the received chunk with the smallest
        # index).
        self.chunk_to_play = chunk_number
        self.lg.debug(f"{self.ext_id}: position in the buffer of the first chunk to play={self.chunk_to_play}")

        while (chunk_number < self.chunk_to_play) or (((chunk_number - self.chunk_to_play) % self.buffer_size) < (self.buffer_size // 2)):
            (chunk_number, _) = self.process_next_message()
            if self.player_connected == False:
                break
            while (chunk_number < self.chunk_to_play):
                (chunk_number, _) = self.process_next_message()
                if self.player_connected == False:
                    break
        self.prev_received_chunk = chunk_number

        if __debug__:
            buffering_time = time.time() - start_time
            self.lg.debug(f"{self.ext_id}: buffering time={buffering_time}")
        stderr.write(f" {buffering_time:.2f}")

    def run(self):
        self.lg.debug(f"{self.ext_id}: waiting for the chunks ...")
        for i in range(self.buffer_size):
            self.buffer.append(self.empty_entry_in_buffer())  # L == Lost
            #self.buffer.append((-1, b'L', (None, 0)))  # L == Lost

        self.buffer_data()
        #while (not self.is_the_player_disconected() or self.waiting_for_goodbye):
        while(self.player_connected and self.waiting_for_goodbye):
            self.buffer_and_play()
            # The goodbye messages sent to the splitter can be
            # lost. Therefore, it's a good idea to keep sending
            # [goodbye]'s to the splitter until the [goodbye] from the
            # splitter arrives.
            #if self.player_disconected() or self.received_goodbye():
            #    break

        for i in range(10):
            self.say_goodbye(self.splitter)
        self.say_goodbye_to_the_team()

        # Send pending chunks
        for peer, chunks in self.pending.items():
            for chunk in chunks:
                self.send_chunk_to_peer(chunk, peer)

        self.team_socket.close()

        if __debug__:
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
            self.lg.debug(f"{self.ext_id}: average_neighborhood_degree={avg} ({total_lengths}/{entries})") # Wrong!!!!!!!!!!!!!!!!!!!!!

            self.lg.debug(f"{self.ext_id}: forward = {self.forward}")

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
