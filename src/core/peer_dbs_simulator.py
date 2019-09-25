"""
@package simulator
peer_dbs_simulator module
"""

# Specific simulator behavior.

import time
import sys
import struct
import random
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
#from .simulator_stuff import Simulator_socket as socket
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .peer_dbs import Peer_DBS
import logging
#import colorama
from .chunk_structure import ChunkStructure

class Peer_DBS_simulator(Peer_DBS):

    def __init__(self, id, name = "Peer_DBS_simulator"):
        super().__init__()
        logging.basicConfig(stream=sys.stdout, format="%(asctime)s.%(msecs)03d %(message)s %(levelname)-8s %(name)s %(pathname)s:%(lineno)d", datefmt="%H:%M:%S")
        self.lg = logging.getLogger(__name__)
        self.lg.setLevel(logging.DEBUG)
        self.name = name
        #colorama.init()
        self.lg.info(f"{name}: DBS initialized")

    def listen_to_the_team(self):
        super().listen_to_the_team()
        self.lg.info(f"{self.ext_id}: listening to the team")

    def receive_the_public_endpoint(self):
        super().receive_the_public_endpoint()
        self.lg.info(f"{self.public_endpoint}: received public_endpoint")

    def receive_the_buffer_size(self):
        super().receive_the_buffer_size()
        self.lg.info(f"{self.ext_id}: buffer_size={self.buffer_size}")

    def receive_the_number_of_peers(self):
        super().receive_the_number_of_peers()
        self.lg.info(f"{self.ext_id}: number_of_peers={self.number_of_peers}")

    def receive_the_peer_index_in_team(self):
        super().receive_the_peer_index_in_team()
        self.lg.info(f"{self.ext_id}: peer_index_in_team={self.peer_index_in_team}")

    def say_hello(self, entity):
        super().say_hello(entity)
        self.lg.info(f"{self.ext_id}: sent [hello] to {entity}")

    def receive_the_list_of_peers__peer_feedback(self, peer):
        self.lg.info(f"{self.ext_id}: peer {peer} is in the team")

    def receive_the_list_of_peers__forward_feedback(self):
        self.lg.info(f"{self.ext_id}: forward={self.forward}")

    def receive_the_list_of_peers__pending_feedback(self):
        self.lg.info(f"{self.ext_id}: pending={self.pending}")

    def connect_to_the_splitter__error_feedback(self, error):
        self.lg.error(f"{self.public_endpoint}: {error} when connecting to the splitter {self.splitter}")

    def connect_to_the_splitter(self, peer_port):
        self.lg.info(f"{self.public_endpoint}: connecting to the splitter at {self.splitter}")
        if super().connect_to_the_splitter(peer_port):
            self.lg.info(f"{self.public_endpoint}: I am a peer")
            self.lg.info(f"{self.public_endpoint}: connected to the splitter at {self.splitter}")
            return True
        else:
            self.lg.error(f"{self.public_endpoint}: unable to connect to the splitter at {self.splitter}")
            return False

    def buffer_chunk__buffering_feedback(self, chunk_number, chunk_data, origin, sender, position):
        self.lg.info(f"{self.ext_id}: buffering ({chunk_number}, {chunk_data}, {origin}) received from {sender} in position {position}")

    def send_chunks_to_neighbors(self):
        self.lg.info(f"{self.ext_id}: sending chunks to neighbors (pending={self.pending})")
        Peer_DBS.send_chunks_to_neighbors(self)

    def process_chunk(self, chunk_number, origin, chunk_data, sender):
        self.lg.info(f"{self.ext_id}: processing chunk {chunk_number} received from {sender} originated by {origin}")
        Peer_DBS.process_chunk(self, chunk_number, origin, chunk_data, sender)
        
    def process_chunk__show_fanout(self):
        self.rounds_counter += 1
        for origin, neighbors in self.forward.items():
            buf = ''
            #for i in neighbors:
            #    buf += str(i)
            buf = len(neighbors)*"#"
            self.lg.debug(f"{self.ext_id}: round={self.rounds_counter:03} origin={origin} K={len(neighbors):02} fan-out={buf:10}")

    def process_chunk__show_CLR(self, chunk_number):
        try:
            CLR = self.number_of_lost_chunks / (chunk_number - self.prev_chunk_number_round)
            self.lg.info(f"{self.ext_id}: CLR={CLR:1.3} losses={self.number_of_lost_chunks} chunk_number={chunk_number} increment={chunk_number - self.prev_chunk_number_round}")
        except ZeroDivisionError:
            pass
        self.prev_chunk_number_round = chunk_number

    def update_pendings(self, origin, chunk_number):
        self.lg.info(f"{self.ext_id}: updating pendings (origin={origin}, chunk_number={chunk_number})")
        Peer_DBS.update_pendings(self, origin, chunk_number)

    def compose_message__show(self, chunk_position, chunk_number):
        self.lg.info(f"{self.ext_id}: chunk_position={chunk_position} chunk_number={self.buffer[chunk_position][ChunkStructure.CHUNK_NUMBER]} origin={self.buffer[chunk_position][ChunkStructure.ORIGIN]}")

    def send_chunk_to_peer(self, chunk_number, destination):
        self.lg.info(f"{self.ext_id}: chunk {chunk_number} sent to {destination}")
        super().send_chunk_to_peer(chunk_number, destination)

    def process_hello(self, sender):
        self.lg.info(f"{self.ext_id}: received [hello] from {sender}")
        super().process_hello(sender)

    def process_goodbye__warning(self, sender, peers_list):
        self.lg.warning(f"{self.ext_id}: failed to remove peer {sender} from {peers_list}")

    def process_goodbye(self, sender):
        self.lg.info(f"{self.ext_id}: received [goodbye] from {sender}")
        super().process_goodbye(sender)

    def process_unpacked_message__warning(self, chunk_number):
        self.lg.warning("{self.ext_id}: unexpected control chunk of index={chunk_number}")

    def send_chunks(self, neighbor):
        self.lg.info(f"{self.ext_id}: sending chunks neighbor={neighbor} pending[{neighbor}]={self.pending[neighbor]}")
        super().send_chunks(neighbor)

    def request_chunk(self, chunk_number, peer):
        super().request_chunk(chunk_number, peer)
        self.lg.info(f"{self.ext_id}: sent [request {chunk_number}] to {peer}")

    def play_chunk__show_buffer(self):
        #sys.stderr.write(f" {len(self.forward)}"); sys.stderr.flush()
        buf = ""
        for i in self.buffer:
            if i[ChunkStructure.CHUNK_DATA] != b'L':
                try:
                    _origin = list(self.forward[self.public_endpoint]).index(i[ChunkStructure.ORIGIN])
                    buf += hash(_origin)
                except ValueError:
                    buf += '-' # Peers do not exist in their forwarding table.
            else:
                buf += " "
        self.lg.debug(f"{self.ext_id}: buffer={buf}")

    def play_chunk__lost_chunk_feedback(self):
        self.lg.warning(f"{self.ext_id}: play_chunk: lost chunk! {self.chunk_to_play} (number_of_lost_chunks={self.number_of_lost_chunks})")

    def say_goodbye_to_the_team(self):
        super().say_goodbye_to_the_team()
        self.lg.info(f"{self.ext_id}: sent [goodbye] to the team")

    def buffer_data__show_first_chunk_to_play(self):
        self.lg.info(f"{self.ext_id}: position in the buffer of the first chunk to play={self.chunk_to_play}")

    def buffer_data(self):
        self.lg.info(f"{self.ext_id}: buffering")
        start_time = time.time()
        super().buffer_data()
        buffering_time = time.time() - start_time
        self.lg.info(f"{self.ext_id}: buffering time={buffering_time}")

    def run(self):
        self.lg.info(f"{self.ext_id}: waiting for the chunks ...")
        super().run()
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

    def provide_CLR_feedback(self, sender):
        if sender == self.splitter:
            if self.played > 0 and self.played >= self.number_of_peers:
                CLR = self.number_of_lost_chunks / (self.played + self.number_of_lost_chunks) # Chunk Loss Ratio
