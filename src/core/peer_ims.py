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

import netifaces
from selectors import select
import struct
import random
import logging
from .common import Common
from .simulator_stuff import Simulator_socket as socket
from core.peer_dbs import Peer_DBS

class Peer_IMS(Peer_DBS):

    def __init__(self, id, name, loglevel):
        super().__init__(id, name, loglevel)

    def listen_to_the_team(self):
        Peer_DBS.listen_to_the_team(self)
        self.mcast_socket = socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mcast_socket.bind(('', 1234)) # Listen any interface,
                                           # including 224.0.0.1
        self.lg.debug("{}: port 1234 bound to 0.0.0.0".format(self.ext_id))
    
    def receive_the_list_of_peers(self):
        iface = netifaces.interfaces()[1]      # Name of the second interface
        stuff = netifaces.ifaddresses(iface)   # Configuration data
        IP_stuff = stuff[netifaces.AF_INET][0] # Only the IP stuff
        netmask = IP_stuff['netmask']          # Get netmask
        address = IP_stuff['addr']             # Get local IP addr
        self.int32_netmask = socket.ip2int(netmask) # Netmask as an integer
        int32_address = socket.ip2int(address) # IP address as an integer
        int32_network_address = int32_address & self.int32_netmask
        if __debug__:
            network_address = socket.int2ip(int32_network_address)
            self.lg.info("{}: network address = {}".format(self.ext_id, network_address))
        self.index_of_peer = {}
        peers_pending_of_reception = self.number_of_peers
        msg_length = struct.calcsize("!Ii")
        counter = 0
        #isolations = 0
        self.forward[self.id] = []
        while peers_pending_of_reception > 0:
            msg = self.splitter_socket.recv(msg_length)
            peer = struct.unpack("!Ii", msg)
            peer = (socket.int2ip(peer[0]),peer[1])
            self.team.append(peer)
            int32_peer_address = socket.ip2int(peer[0])
            int32_peer_network_address = int32_peer_address & self.int32_netmask
            #print("--------------", socket.int2ip(int32_network_address), socket.int2ip(int32_peer_network_address))
            # Check for peers running in the same subnet
            if int32_network_address == int32_peer_network_address:
                self.lg.debug("{}: peer {} running in the same local network".format(self.ext_id, peer))
                if ("224.0.0.1", 1234) not in self.forward[self.id]:
                    self.forward[self.id].append(("224.0.0.1", 1234))
                self.pending[("224.0.0.1", 1234)] = []
            else:
                if counter >= self.number_of_monitors: # Monitors never are isolated
                    r = random.random()
                    if r <= self.link_failure_prob:
                        self.team_socket.isolate(self.id, peer)
                        self.lg.info("{}: {} isolated of {}".format(self.ext_id, self.id, peer))
                #print("{}: peer={}".format(self.ext_id, peer))
                #self.forward[self.id].append(peer)
                #self.pending[peer] = []

            self.say_hello(peer)
            self.lg.debug("{}: peer {} is in the team".format(self.ext_id, peer))
            self.index_of_peer[peer] = counter
            counter += 1
            peers_pending_of_reception -= 1

        self.lg.debug("{}: forward={} pending={}".format(self.ext_id, self.forward, self.pending))

    def receive_packet(self):
        self.lg.debug("{}: waiting for a packet ...".format(self.ext_id))
        ready_socks, _, _ = select.select([self.team_socket, self.mcast_socket], [], [])
        for sock in ready_socks:
            return sock.recvfrom(self.max_pkg_length)
        
    def process_hello(self, sender):
        if (socket.ip2int(sender[0]) & self.int32_netmask) == (socket.ip2int(self.id[0]) & self.int32_netmask):
            self.lg.debug("{}: received [hello] from {}".format(self.ext_id, sender))
            if ('224.0.0.1', 1234) not in self.forward[self.id]:
                self.forward[self.id].append(('224.0.0.1', 1234))
                self.pending[('224.0.0.1', 1234)] = []
        else:
            super().process_hello(sender)            

    def process_goodbye(self, sender):
        if (socket.ip2int(sender[0]) & self.int32_netmask) == (socket.ip2int(self.id[0]) & self.int32_netmask):
            self.lg.debug("{}: received [goodbye] from {}".format(self.ext_id, sender))
        else:
            super().process_goodbye(sender)

    def add_new_forwarding_rule(self, peer, neighbor):
        if peer[0] != self.id[0]:
            super().add_new_forwarding_rule(peer, neighbor)
