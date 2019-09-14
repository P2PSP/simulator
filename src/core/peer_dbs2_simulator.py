"""
@package simulator
peer_dbs_simulator module
"""

# Specific simulator behavior.

import sys
import struct
import random
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
#from .simulator_stuff import Simulator_socket as socket
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .peer_dbs2 import Peer_DBS2
from .peer_dbs_simulator import Peer_DBS_simulator
import logging

class Peer_DBS2_simulator(Peer_DBS2, Peer_DBS_simulator):

    def __init__(self, id, name = "Peer_DBS2_simulator", loglevel=logging.ERROR):
        Peer_DBS2.__init__(self)
        Peer_DBS_simulator.__init__(self, id, name, loglevel)
        self.lg = logging.getLogger(name)
        self.lg.setLevel(loglevel)
        self.name = name
        #colorama.init()
        self.lg.info(f"{name}: DBS2 initialized")

#    chunks_before_leave = 999999

#    def receive_buffer_size(self):
#        super().receive_buffer_size()
#        self.sender_of_chunks = [""] * self.buffer_size

#    def receive_the_list_of_peers__simulation(self, counter, peer):
#        if counter >= self.number_of_monitors: # Monitors never are isolated
#            r = random.random()
#            if r <= self.link_failure_prob:
#                self.team_socket.isolate(self.public_endpoint, peer)
#                self.lg.info("f{self.ext_id}: {self.public_endpoint} isolated of {peer}")

    def send_peer_type(self):
        if(self._id[0:2]=='MP'):
            msg = struct.pack('!H',2)    # Malicious Peer
        elif(self._id[0]=='M'):
            msg = struct.pack('!H',0)    # Monitor Peer
        else:
            msg = struct.pack('!H',1)    # Regular Peer
        self.splitter_socket.send(msg)

    def map_peer_type(self,real_id):
        if sim.FEEDBACK:
            if self._id[0] == 'M':
                if self._id[1] == 'P':
                    sim.FEEDBACK["DRAW"].put(("MAP",','.join(map(str,real_id)),"MP"))
                else:
                    sim.FEEDBACK["DRAW"].put(("MAP",','.join(map(str,real_id)),"M"))
            else:
                sim.FEEDBACK["DRAW"].put(("MAP",','.join(map(str,real_id)),"P"))    

    def connect_to_the_splitter(self, peer_port):
        super().connect_to_the_splitter(peer_port)
        # S I M U L A T I O N
        if self.public_endpoint[0] != None:
            self.map_peer_type(self.public_endpoint); # Maybe at the end of this
            # function to be easely extended
            # in the peer_dbs_sim class.

    def provide_request_feedback(self, sender):
        if sim.FEEDBACK:
            sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str,sender)) ))
            sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", ','.join(map(str,self.public_endpoint)), ','.join(map(str,sender))))

    def provide_hello_feedback(self, sender):
        if sim.FEEDBACK:
            sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str,sender))))
            sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", ','.join(map(str,self.public_endpoint)), ','.join(map(str,sender))))

    def provide_CLR_feedback(self, sender):
        if sender == self.splitter:
            if self.played > 0 and self.played >= self.number_of_peers:
                CLR = self.number_of_lost_chunks / (self.played + self.number_of_lost_chunks) # Chunk Loss Ratio
                if sim.FEEDBACK:
                    sim.FEEDBACK["DRAW"].put(("CLR", ','.join(map(str,self.public_endpoint)), CLR))

    #def check__player_connected(self):
    #    #self.received_chunks += 1
    #    if (self.received_chunks >= Peer_DBS_simulator.chunks_before_leave):
    #        self.player_connected = False

    #def compose_goodbye_message(self):
    #    msg = struct.pack("!iii", Message.GOODBYE, self.number_of_chunks_consumed, self.number_of_lost_chunks)
    #    return msg   
