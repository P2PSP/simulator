"""
@package simulator
peer_ims module
"""

# IMS (Ip Multicast Set) of rules

# When the list of peers is received from the splitter, for all those
# peers that share the same network address that the peer, the
# endpoint 224.0.0.1:1234 will be used. Thus, when the peer receives a
# chunk from the splitter, it will forward it to this multicast
# channel (all hosts multicast group). The rest of the logic is identical?

from selectors import select
import struct
import random
from .simulator_stuff import Simulator_socket as socket
from core.peer_dbs import Peer_DBS

class Peer_IMS(Peer_DBS):

    def listen_to_the_team(self):
        Peer_DBS.listen_to_the_team(self)
        self.mcast_socket = socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mcast_socket.bind(('', 1234)) # Listen any interface,
                                           # including 224.0.0.1
        self.lg.debug("{}: port 1234 bound to 0.0.0.0".format(self.ext_id))
    
    def receive_the_list_of_peers(self):
        self.index_of_peer = {}
        peers_pending_of_reception = self.number_of_peers
        msg_length = struct.calcsize("li")
        counter = 0
        #isolations = 0
        self.forward[self.id] = []
        while peers_pending_of_reception > 0:
            msg = self.splitter_socket.recv(msg_length)
            peer = struct.unpack("li", msg)
            peer = (socket.int2ip(peer[0]),peer[1])

            # Check for peers running in the same subnet
            if self.id[0] == peer[0]:
                peer = ("224.0.0.1", 1234)
                if peer not in self.forward[self.id]:
                    self.forward[self.id].append(peer)
            # S I M U L A T O R
            else:
                if counter >= self.number_of_monitors: # Monitors never are isolated
                    r = random.random()
                    if r <= self.link_loss_ratio:
                        self.team_socket.isolate(self.id, peer)
                        self.lg.info("{}: {} isolated of {}".format(self.ext_id, self.id, peer))
                
                self.say_hello(peer)
                self.lg.debug("{}: peer {} is in the team".format(self.ext_id, peer))
                #print("{}: peer={}".format(self.ext_id, peer))
                self.forward[self.id].append(peer)

            self.pending[peer] = []
            self.index_of_peer[peer] = counter
            counter += 1
            peers_pending_of_reception -= 1

        self.lg.debug("{}: forward={} pending={}".format(self.ext_id, self.forward, self.pending))

    def receive_packet(self):
        ready_socks, _, _ = select.select([self.team_socket,
                                           self.mcast_socket], [], [])
        for sock in ready_socks:
            return sock.recvfrom(self.max_msg_length)
        
    def process_hello(self, sender):
        if sender not in self.forward[self.id]:
            if sender[0] == self.id[0]:
                if ('224.0.0.1', 1234) not in self.forward[self.id]:
                    self.forward[self.id].append(('224.0.0.1', 1234))
            else:
                self.forward[self.id].append(sender)
            self.pending[sender] = []
            self.lg.info("{}: inserted {} in forward[{}] by [hello] from {} (forward={})".format(self.ext_id, sender, self.id, sender, self.forward))
            self.debt[sender] = 0

            # S I M U L A T I O N
            if sim.FEEDBACK:
                sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str,sender))))
                sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", ','.join(map(str,self.id)), ','.join(map(str,sender))))
            
