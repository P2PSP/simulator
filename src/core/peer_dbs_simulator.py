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
from .simulator_stuff import Simulator_socket as socket
from .simulator_stuff import hash
from .peer_dbs import Peer_DBS

# quitar
MAX_DEGREE = 5

class Peer_DBS_simulator(Peer_DBS):
    chunks_before_leave = 999999

    def receive_buffer_size(self):
        super().receive_buffer_size()
        self.sender_of_chunks = [""] * self.buffer_size

    def receive_the_list_of_peers(self):
        self.index_of_peer = {}
        peers_pending_of_reception = self.number_of_peers
        msg_length = struct.calcsize("!Ii")
        counter = 0

        # Peer self.id will forward by default all chunks originated
        # at itself.
        self.forward[self.public_endpoint] = []
        
        while peers_pending_of_reception > 0:
            msg = self.splitter_socket.recv(msg_length)
            peer = struct.unpack("!Ii", msg)
            peer = (socket.int2ip(peer[0]),peer[1])
            self.team.append(peer)
            self.lg.debug("{}: team={}".format(self.ext_id, self.team))
            self.forward[self.public_endpoint].append(peer)
            self.index_of_peer[peer] = counter
            self.debts[peer] = 0
            self.lg.debug("{}: debs={}".format(self.ext_id, self.debts))
            
            # S I M U L A T O R
            if counter >= self.number_of_monitors: # Monitors never are isolated
                r = random.random()
                if r <= self.link_failure_prob:
                    self.team_socket.isolate(self.public_endpoint, peer)
                    self.lg.critical("{}: {} isolated of {}".format(self.ext_id, self.public_endpoint, peer))
                
            self.say_hello(peer)
            self.lg.debug("{}: peer {} is in the team".format(self.ext_id, peer))
            counter += 1
            peers_pending_of_reception -= 1

        self.lg.debug("{}: forward={} pending={}".format(self.ext_id, self.forward, self.pending))

    # S I M U L A T I O N
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
        if self.id!=None:
            self.map_peer_type(self.id); # Maybe at the end of this
            # function to be easely extended
            # in the peer_dbs_sim class.

    def process_request(self, chunk_number, sender):

        # If a peer X receives [request Y] from peer Z, X will
        # append Z to forward[Y.origin].

        origin = self.chunks[chunk_number % self.buffer_size][Common.ORIGIN]

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

            # S I M U L A T I O N
            if sim.FEEDBACK:
                sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str,sender)) ))
                sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", ','.join(map(str,self.public_endpoint)), ','.join(map(str,sender))))
        else:
            # Otherwise, I can't help.
            self.lg.debug("{}: request received from {}, but I haven't the requested chunk {}".format(self.ext_id, sender, chunk_number))

        self.lg.debug("{}: chunk={} origin={} forward={}".format(self.ext_id, self.chunks[chunk_number % self.buffer_size], origin, self.forward))
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

        if sender not in self.forward[self.public_endpoint]:
            self.forward[self.public_endpoint].append(sender)
            self.pending[sender] = []
            self.lg.info("{}: inserted {} in forward[{}] by [hello] from {} (forward={})".format(self.ext_id, sender, self.public_endpoint, sender, self.forward))

            # S I M U L A T I O N
            if sim.FEEDBACK:
                sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str,sender))))
                sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", ','.join(map(str,self.public_endpoint)), ','.join(map(str,sender))))
        self.team.append(sender)
        self.debts[sender] = 0
        self.number_of_peers += 1
        self.lg.debug("{}: inserted {} in {}".format(self.ext_id, sender, self.team))
        self.lg.debug("{}: inserted {} in {}".format(self.ext_id, sender, self.debts))

    # DBS peer's logic
    def process_unpacked_message(self, message, sender):

        chunk_number = message[Common.CHUNK_NUMBER]

        if chunk_number >= 0:

            # We have received a chunk.
            chunk_data = message[Common.CHUNK_DATA]
            origin = message[Common.ORIGIN]

            # Compute deltas
            self.chunk_number_delta = chunk_number - self.chunk_number_delta
            #self.chunk_number_delta = chunk_number - self.prev_received_chunk
            self.lg.info("{}: delta of chunk {} is {}".format(self.ext_id, chunk_number, self.chunk_number_delta))
            self.chunk_number_delta = chunk_number

            # S I M U L A T I O N
            if sender == self.splitter:
                if self.played > 0 and self.played >= self.number_of_peers:
                    CLR = self.losses / (self.played + self.losses) # Chunk Loss Ratio
                    if sim.FEEDBACK:
                        sim.FEEDBACK["DRAW"].put(("CLR", ','.join(map(str,self.public_endpoint)), CLR))

            # 1. Store or report duplicates
            if self.chunks[chunk_number % self.buffer_size][Common.CHUNK_NUMBER] == chunk_number:
                # Duplicate chunk. Ignore it and warn the sender to
                # stop sending more chunks from the origin of the received
                # chunk "chunk_number".
                self.lg.debug("{}: duplicate chunk {} from {} (the first one was sent by {}) BUFFER={}".format(self.ext_id, chunk_number, sender, self.chunks[chunk_number % self.buffer_size][Common.ORIGIN], self.chunks))
                self.prune_origin(chunk_number, sender)
            else:
                self.buffer_new_chunk(chunk_number, chunk_data, origin, sender)
                
                # Showing buffer
                buf = ""
                for i in self.chunks:
                    if i[Common.CHUNK_NUMBER] > -1:
                        try:
                            #peer_number = self.index_of_peer[i[Common.ORIGIN]]
                            peer_number = self.team.index(i[Common.ORIGIN])
                            buf += hash(peer_number)
                        except ValueError:
                            buf += '-'
                            #self.index_of_peer[i[Common.ORIGIN]] = self.number_of_peers
                            #peer_number = self.number_of_peers
                            self.number_of_peers += 1
                        #buf += hash(peer_number)
                        #buf += '-'
                    else:
                        buf += " "
                self.lg.debug("{}: buffer={}".format(self.ext_id, buf))

                # S I M U L A T I O N
                self.received_chunks += 1
                if (self.received_chunks >= Peer_DBS_simulator.chunks_before_leave):
                    self.player_connected = False

                if sender == self.splitter:
                    for peer, debt in self.debts:
                        debt //= 2
                    self.rounds_counter += 1
                    for peer, peer_list in self.forward.items():
                        if len(peer_list) > 0:
                            buf = len(peer_list)*"#"
                            self.lg.debug("{}: degree({})) {}".format(self.ext_id, peer, buf))
                else:
                    self.lg.debug("--------- sender={} splitter={}".format(sender, self.splitter))
                    self.debts[sender] -= 1
                    self.lg.debug("{}: debts={}".format(self.ext_id, self.debts))
                    self.add_new_forwarding_rule(self.public_endpoint, sender)
                    self.lg.debug("{}: forward={}".format(self.ext_id, self.forward))
                if origin in self.forward:
                    self.update_pendings(origin, chunk_number)

                if len(self.pending) > 0:
                    self.neighbor = list(self.pending.keys())[(self.neighbor_index) % len(self.pending)]
                    self.send_chunks()
                    self.neighbor_index = list(self.pending.keys()).index(self.neighbor) + 1

        else:  # message[Common.CHUNK_NUMBER] < 0

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

    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number % self.buffer_size][Common.CHUNK_NUMBER] > -1:
            self.chunks[chunk_number % self.buffer_size] = (-1, b'L', None)
            self.played += 1
            #sys.stdout.write('o'); sys.stdout.flush()
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
            #destination = self.chunks[i % self.buffer_size][Common.ORIGIN]
            #while destination == None:
            #    i += 1
            #    destination = self.chunks[i % self.buffer_size][Common.ORIGIN]
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

            if len(self.team)>1:
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

