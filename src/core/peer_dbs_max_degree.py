"""
@package simulator
peer_dbs_max_degree module
"""

import random
import struct

from .peer_dbs import Peer_DBS
from .simulator_stuff import Simulator_socket as socket
from .simulator_stuff import Simulator_stuff as sim


class Peer_DBS_max_degree(Peer_DBS):

    MAX_DEGREE = 5

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
            peer = (socket.int2ip(peer[0]), peer[1])
            self.team.append(peer)
            if counter < self.MAX_DEGREE:
                self.forward[self.id].append(peer)
            self.index_of_peer[peer] = counter

            # S I M U L A T O R
            if counter >= self.number_of_monitors:  # Monitors never are isolated
                r = random.random()
                if r <= self.link_failure_prob:
                    self.team_socket.isolate(self.id, peer)
                    self.lg.critical("{}: {} isolated of {}".format(self.ext_id, self.id, peer))

            self.say_hello(peer)
            self.lg.debug("{}: peer {} is in the team".format(self.ext_id, peer))
            counter += 1
            peers_pending_of_reception -= 1

        self.lg.debug("{}: forward={} pending={}".format(self.ext_id, self.forward, self.pending))

    def add_new_forwarding_rule(self, peer, neighbor):
        if len(self.forward[peer]) < self.MAX_DEGREE:
            self.lg.debug("{}: {} adding new neighbor {}".format(self.ext_id, peer, neighbor))
            try:
                if neighbor not in self.forward[peer]:
                    self.forward[peer].append(neighbor)
                    self.pending[neighbor] = []
            except KeyError:
                self.forward[peer] = [neighbor]
                self.pending[neighbor] = []

    def process_request(self, chunk_number, sender):
        # If a peer X receives [request Y] from peer Z, X will
        # append Z to forward[Y.origin].

        origin = self.chunks[chunk_number % self.buffer_size][self.ORIGIN]

        self.lg.debug("{}: received [request {}] from {} (origin={}, forward={})".format(
            self.ext_id, chunk_number, sender, origin, self.forward))

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
                    if len(self.forward[origin]) >= self.MAX_DEGREE:
                        a_peer = random.choice(self.forward[origin])
                        self.forward[origin].remove(a_peer)
                        self.lg.debug("{}: removed peer {} by excess".format(self.ext_id, a_peer))

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
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str, sender))))
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", ','.join(
                        map(str, self.id)), ','.join(map(str, sender))))
        else:
            # Otherwise, I can't help.
            if __debug__:
                self.lg.debug("{}: request received from {}, but I haven't the requested chunk {}".format(
                    self.ext_id, sender, chunk_number))

        self.lg.debug("{}: chunk={} origin={} forward={}".format(
            self.ext_id, self.chunks[chunk_number % self.buffer_size], origin, self.forward))
        self.lg.debug("{}: length_forward={} forward={}".format(self.ext_id, len(self.forward), self.forward))

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

        if len(self.forward[self.id]) < self.MAX_DEGREE:
            if sender not in self.forward[self.id]:
                self.forward[self.id].append(sender)
                self.pending[sender] = []
                self.lg.info("{}: inserted {} in forward[{}] by [hello] from {} (forward={})".format(
                    self.ext_id, sender, self.id, sender, self.forward))
                self.debt[sender] = 0

                if __debug__:
                    # S I M U L A T I O N
                    if sim.FEEDBACK:
                        sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str, sender))))
                        sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", ','.join(
                            map(str, self.id)), ','.join(map(str, sender))))
        self.team.append(sender)
