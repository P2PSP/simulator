"""
@package simulator
peer_dbs module
"""

# DBS (Data Broadcasting Set) layer

# DBS peers receive chunks from the splitter and other peers, and
# resend them, depending on the forwarding requests performed by the
# peers. In a nutshell, if a peer X wants to receive from peer Y
# the chunks from origin Z, X must request it to Y, explicitally.

import random
import struct
import time
from threading import Thread

from .common import Common
from .peer_dbs import Peer_DBS
from .simulator_stuff import Simulator_socket as socket
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import hash


class Peer_DBS_latency(Peer_DBS):

    CHUNK_TIME = 3

    def __init__(self, id, name):
        super().__init__(id, name)
        self.max_pkg_length = struct.calcsize("islid")

    def process_message(self):
        try:
            pkg, sender = self.receive_packet()
            # self.lg.debug("{}: received {} from {} with length {}".format(self,id, pkg, sender, len(pkg)))
            if len(pkg) == self.max_pkg_length:
                msg = struct.unpack("islid", pkg)
                # Data message: [chunk number, chunk, origin, (address and port), time stamp]
                message = msg[self.CHUNK_NUMBER], msg[self.CHUNK_DATA], (socket.int2ip(
                    msg[self.ORIGIN]), msg[self.ORIGIN+1]), msg[self.CHUNK_TIME+1]
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
            # self.say_goodbye(self.splitter)
            # self.say_goodbye_to_the_team()
            raise
        except struct.error:
            self.lg.error("{}: packet length={}".format(self.ext_id, len(pkg)))
            raise
        #    return (0, self.id)

    def compose_message(self, chunk_number):
        chunk_position = chunk_number % self.buffer_size
        chunk = self.chunks[chunk_position]
        stored_chunk_number = chunk[self.CHUNK_NUMBER]
        chunk_data = chunk[self.CHUNK_DATA]
        chunk_origin_IP = chunk[self.ORIGIN][0]
        chunk_origin_port = chunk[self.ORIGIN][1]
        time_stamp = chunk[self.CHUNK_TIME]
        message = (stored_chunk_number, chunk_data, socket.ip2int(chunk_origin_IP), chunk_origin_port, time_stamp)
        packet = struct.pack("islid", *message)
        return packet

    def buffer_new_chunk(self, chunk_number, chunk_data, origin, time_stamp, sender):
        self.lg.debug("{}: received chunk {} from {}".format(
            self.ext_id, (chunk_number, chunk_data, origin, time_stamp), sender))
        # New chunk. (chunk_number, chunk, origin) -> buffer[chunk_number]
        self.chunks[chunk_number % self.buffer_size] = (chunk_number, chunk_data, origin, time_stamp)

    # DBS peer's logic
    def process_unpacked_message(self, message, sender):

        chunk_number = message[self.CHUNK_NUMBER]

        if chunk_number >= 0:

            # We have received a chunk.
            chunk_data = message[self.CHUNK_DATA]
            origin = message[self.ORIGIN]
            time_stamp = message[self.CHUNK_TIME]
            now = time.time()
            latency = now - time_stamp
            print("latency={}".format(latency))

            # Compute deltas
            self.chunk_number_delta = chunk_number - self.chunk_number_delta
            #self.chunk_number_delta = chunk_number - self.prev_received_chunk
            self.lg.info("{}: delta of chunk {} is {}".format(self.ext_id, chunk_number, self.chunk_number_delta))
            self.chunk_number_delta = chunk_number

            if __debug__:
                # S I M U L A T I O N
                if sender == self.splitter:
                    if self.played > 0 and self.played >= self.number_of_peers:
                        CLR = self.losses / (self.played + self.losses)  # Chunk Loss Ratio
                        if sim.FEEDBACK:
                            sim.FEEDBACK["DRAW"].put(("CLR", ','.join(map(str, self.id)), CLR))
                        # self.losses = 0 # Ojo, puesto a 0 para calcular CLR
                        # self.played = 0 # Ojo, puesto a 0 para calcular CLR

            # 1. Store or report duplicates
            if self.chunks[chunk_number % self.buffer_size][self.CHUNK_NUMBER] == chunk_number:
                # Duplicate chunk. Ignore it and warn the sender to
                # stop sending more chunks from the origin of the received
                # chunk "chunk_number".
                self.lg.debug("{}: duplicate chunk {} from {} (the first one was sent by {}) BUFFER={}"
                              .format(self.ext_id, chunk_number, sender,
                                      self.chunks[chunk_number % self.buffer_size][self.ORIGIN], self.chunks))
                self.prune_origin(chunk_number, sender)
            else:
                self.buffer_new_chunk(chunk_number, chunk_data, origin, time_stamp, sender)

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
                    # if sender in self.debt:
                    #    self.debt[sender] -= 1
                    # else:
                    #    self.debt[sender] = -1
                    # Usar mejor técnica de ir dividiendo entre 2 cada round
                    # if self.neighbor is None:  # Quizás se pueda quitar!!!!
                    #self.neighbor = sender
                    # try:
                    #    if sender not in self.forward[self.id]:
                    #        self.forward[self.id].append(sender)
                    #        self.pending[sender] = []
                    # except KeyError:
                    #    self.forward[self.id] = [sender]
                    #    self.pending[sender] = []
                    self.add_new_forwarding_rule(self.id, sender)
                    self.lg.debug("{}: forward={}".format(self.ext_id, self.forward))
                    # for peer in self.forward:
                if origin in self.forward:
                    self.update_pendings(origin, chunk_number)
                # When a peer X receives a chunk (number) C with origin O,
                # for each peer P in forward[O], X performs
                # pending[P].append(C).
                # if origin in self.forward:  # True: #len(self.forward[origin]) > 0: #True: #origin != self.id:
                #    for P in self.forward[origin]:
                    # if P in self.pending:
                #        self.pending[P].append(chunk_number)
                    # else:
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
                # if len(self.forward[self.id]) < self.max_degree:
                self.process_hello(sender)
            elif chunk_number == Common.GOODBYE:
                self.process_goodbye(sender)
            else:
                self.lg.info("{}: unexpected control chunk of index={}".format(self.ext_id, chunk_number))
        return (chunk_number, sender)

    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number % self.buffer_size][self.CHUNK_DATA] == b'C':
            self.chunks[chunk_number % self.buffer_size] = (-1, b'L', None, 0.0)
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
            # while destination == None:
            #    i += 1
            #    destination = self.chunks[i % self.BUFFER_SIZE][self.ORIGIN]
            #self.request_chunk(chunk_number, destination)
            # And remove the peer in forward with higher debt.
            #print("{}: ------------> {}".format(self.ext_id, self.debt))
            # try:
            #    remove = max(self.debt, key=self.debt.get)
            # except ValueError:
            #    remove = self.neighbor
            # self.process_goodbye(remove)

            # We send the request to the neighbor that we have served.
            #self.request_chunk(chunk_number, self.neighbor)

            self.request_chunk(chunk_number, random.choice(self.team))

            # Send the request to all neighbors.
            # for neighbor in self.forward[self.id]:
            #    self.request_chunk(chunk_number, neighbor)

            # Send the request to all the team.
            # for peer in self.team:
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
        # return self.player_connected
