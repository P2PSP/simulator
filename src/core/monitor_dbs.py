"""
@package simulator
monitor_dbs module
"""

import random
import struct
from .simulator_stuff import Simulator_socket as socket
from .common import Common
from .peer_dbs import Peer_DBS

class Monitor_DBS(Peer_DBS):
    def __init__(self, id, name, loglevel):
        #self.losses = 0
        super().__init__(id, name, loglevel)

    def receive_buffer_size(self):
        Peer_DBS.receive_buffer_size(self)
        # self.buffer_size = self.splitter_socket.recv("H")
        # print(self.id, ": received buffer_size =", self.buffer_size, "from S")
        # self.buffer_size //= 2 # To MRS

        # S I M U L A T I O N
        self.sender_of_chunks = [""] * self.buffer_size

    def complain(self, chunk_number):
        msg = struct.pack("!ii", Common.LOST_CHUNK, chunk_number)
        self.team_socket.sendto(msg, self.splitter)
        self.lg.info("{}: [lost chunk {}] sent to {}".format(self.id, chunk_number, self.splitter))

    #def request_chunk(self, chunk_number, peer):
    #    Peer_DBS.request_chunk(self, chunk_number, peer) # super()?
    #    self.complain(chunk_number)

    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number % self.buffer_size][Common.CHUNK_NUMBER] > -1:
            self.chunks[chunk_number % self.buffer_size] = (-1, b'L', None)
            self.played += 1
            #sys.stdout.write('o'); sys.stdout.flush()
        else:
            self.complain(chunk_number)
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
