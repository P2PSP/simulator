"""
@package simulator
peer_dbs2 module
"""

# Abstract class

# DBS2 (Data Broadcasting Set extension 2) layer, peer side.

# DBS2 extends the functionality of DBS considering more origin
# peers. This means that peers can receive the chunks indirectly,
# tracing multihop paths. Peers retrieve these alternatives (to the
# one used in DBS) when chunks are lost.

import struct
import sys
from threading import Thread
from .messages import Messages
from .limits import Limits
from .socket_wrapper import Socket_wrapper as socket
from .simulator_stuff import hash
from .ip_tools import IP_tools
from .chunk_structure import ChunkStructure
from .peer_dbs import Peer_DBS

import random

class Peer_DBS2(Peer_DBS):

    def __init__(self):
        super().__init__('a')
        
        # Peers (end-points) in the known team, which is formed by
        # those peers that has sent to this peer a chunk, directly or
        # indirectly.
        self.team = []

    def send_prune_origin(self, chunk_number, peer):
        #sys.stderr.write(f" {self.ext_id}{chunk_number}{peer}"); sys.stderr.flush()
        msg = struct.pack("!ii", Messages.PRUNE, chunk_number)
        self.team_socket.sendto(msg, peer)
        self.lg.warning(f"{self.ext_id}: [prune {chunk_number}] sent to {peer}")

    def process_chunk(self, chunk_number, origin, chunk_data, sender):
        super().process_chunk(chunk_number, origin, chunk_data, sender)

        # Check duplicate
        position = chunk_number % self.buffer_size
        if self.buffer[position][ChunkStructure.CHUNK_NUMBER] == chunk_number:
            self.lg.warning(f"{self.ext_id}: buffer_chunk: duplicate chunk {chunk_number} from {sender} (the first one was originated by {self.buffer[position][ChunkStructure.ORIGIN]})")
            self.send_prune_origin(chunk_number, sender)

        # Check if new origin to add it to the known team
        if origin not in self.team:
            if origin != self.public_endpoint:
                # In the optimization stage, the peer
                # could request to a neighbor a chunk that
                # should be provided by the splitter (the
                # peer is the origin). If this happens,
                # the peer will receive chunks from
                # neighbors for what he is the origin
                # (that is not good, but neither a fatal
                # error ... the peer will send a prunning
                # message to these neighbors), but the peer
                # should not be added to the team.
                self.team.append(origin)
                self.lg.info(f"{self.ext_id}: buffer_chunk: appended {origin} to team={self.team} by chunk from origin={origin}")

        # Remove empty forwarding tables.
        for _origin in list(self.forward):
            if len(self.forward[_origin]) == 0:
                del self.forward[_origin]

    # If a peer X receives [request chunk] from peer Z, X will
    # append Z to forward[chunk.origin], but only if Z is not the
    # origin of the requested chunk. This last thing can happen if
    # Z requests chunks that will be originated at itself.
    def process_request(self, chunk_number, sender):
        #sys.stderr.write(f" R{self.ext_id}/{chunk_number}/{sender}"); sys.stderr.flush()
        position = chunk_number % self.buffer_size
        if self.buffer[position][ChunkStructure.CHUNK_DATA] != b'L':
            origin = self.buffer[position][ChunkStructure.ORIGIN]
            if origin != sender:
                if origin in self.forward:
                    if sender not in self.forward[origin]:
                        self.forward[origin].append(sender)
                        self.pending[sender] = []
                    else:
                        # sender already in self.forward[origin]
                        pass
                else:
                    # origin is not in self.forward
                    self.forward[origin] = [sender]
                    self.pending[sender] = []
            else:
                # Request ignored
                pass
        else:
            # I haven't the chunk
            pass
        '''
        origin = self.buffer[chunk_number % self.buffer_size][ChunkStructure.ORIGIN]
        if origin != sender:
            self.lg.debug(f"{self.ext_id}: process_request: chunks={self.buffer}")

            self.lg.info(f"{self.ext_id}: process_request: received [request {chunk_number}] from {sender} (origin={origin})")

            # if origin[0] != None:
            if self.buffer[chunk_number % self.buffer_size][ChunkStructure.CHUNK_DATA] != b'L':
                # In this case, I can start forwarding chunks from origin.
                try:
                    self.lg.debug(f"{self.ext_id}: process_request: self.forward[{origin}]={self.forward[origin]} before")
                    if sender not in self.forward[origin]:
                        self.lg.debug(f"{self.ext_id}: process_request: adding {sender} to {self.forward[origin]}")
                        self.forward[origin].append(sender)
                        self.pending[sender] = []
                    else:
                        self.lg.debug(f"{self.ext_id}: process_request: {sender} is already in self.forward[{origin}]={self.forward[origin]}")
                except KeyError:
                    #self.forward[origin] = [sender] # OJOOOOOOOOOOOOOOOOOORRRRRRRRRRRRRRRRRRRRRRRRRRRRRR
                    self.pending[sender] = []
                #self.lg.debug(f"{self.ext_id}: process_request: self.forward[{origin}]={self.forward[origin]} after")
                self.lg.warning(f"{self.ext_id}: process_request: chunks from {origin} will be sent to {sender}")
                self.provide_request_feedback(sender)

                if __debug__:
                    if self.public_endpoint == origin:
                        self.lg.info(f"{self.ext_id}: process_request: sender={sender} added to the primary forwarding table (public_endpoint == origin={origin}) now with length {len(self.forward[self.public_endpoint])}")

            else:
                # I can't help :-(
                self.lg.warning(f"{self.ext_id}: process_request: request received from {sender}, but I have not the requested chunk {chunk_number} in my buffer")

            self.lg.debug(f"{self.ext_id}: process_request: length_forward={len(self.forward)} forward={self.forward}")

        else:
            self.lg.warning(f"{self.ext_id}: process_request: origin={origin} == sender={sender}. Request ignored")
        '''

    # When a {peer} receives a [prune {chunk_number}], the {sender} is
    # requesting that {peer} stop sending chunks originated at
    # {self.buffer[chunk_number % self.buffer_size].origin}.
    def process_prune(self, chunk_number, sender):

        def remove_sender(origin, sender):
            self.lg.debug(f"{self.ext_id}: process_prune: removing {sender} from forward[{origin}]={self.forward[origin]}")
            try:
                self.forward[origin].remove(sender)
                self.lg.warning(f"{self.ext_id}: process_prune: sender={sender} has been removed from forward[{origin}]={self.forward[origin]}")
            except ValueError:
                self.lg.error(f"{self.ext_id}: process_prune: failed to remove peer {sender} from forward={self.forward[origin]} for origin={origin} ")
            if len(self.forward[origin])==0:
                del self.forward[origin]
                if __debug__:
                    if origin in self.forward:
                        self.lg.info(f"{self.ext_id}: process_prune: origin {origin} is still in forward[{origin}]={self.forward[origin]}")
                    else:
                        self.lg.debug(f"{self.ext_id}: process_prune: origin={origin} removed from forward={self.forward}")
            if __debug__:
                if origin == self.public_endpoint:
                    try:
                        self.lg.info(f"{self.ext_id}: process_prune: sender={sender} removed from the primary forwarding table (public_endpoint == origin={origin}) now with length {len(self.forward[self.public_endpoint])}")
                    except KeyError:
                        pass
        
        position = chunk_number % self.buffer_size
        
        # Notice that chunk "chunk_number" should be stored in the
        # buffer because it has been sent to the neighbor that is
        # requesting the prune.
        
        if self.buffer[position][ChunkStructure.CHUNK_NUMBER] == chunk_number:
            origin = self.buffer[position][ChunkStructure.ORIGIN]
            self.lg.warning(f"{self.ext_id}: process_prune: [prune {chunk_number}] received from {sender} for pruning origin={origin}")

            if origin in self.forward:
                self.lg.warning(f"{self.ext_id}: process_prune: origin={origin} is in forward")
                if sender in self.forward[origin]:
                    self.lg.debug(f"{self.ext_id}: process_prune: sender={sender} is in forward[{origin}]")
                    remove_sender(origin, sender)
                else:
                    self.lg.warning(f"{self.ext_id}: process_prune: sender={sender} is not in forward[{origin}]={self.forward[origin]}")
            else:
                self.lg.warning(f"{self.ext_id}: process_prune: origin={origin} is not in forward={self.forward}") 
        else:
            self.lg.warning(f"{self.ext_id}: process_prune: chunk_number={chunk_number} is not in buffer ({self.buffer[position][ChunkStructure.CHUNK_NUMBER]}!={chunk_number})")
            #sys.stderr.write(f"{self.ext_id}: chunk_number={chunk_number} is not in buffer ({self.buffer[position][ChunkStructure.CHUNK_NUMBER]}!={chunk_number})\n")

    def process_hello(self, sender):
        super().process_hello(sender)
        if sender not in self.team:
            if __debug__:
                if sender == self.public_endpoint:
                    self.lg.error(f"{self.ext_id}: appending myself to the team by [hello]")
            self.team.append(sender)
            self.lg.info(f"{self.ext_id}: appended {sender} to team={self.team} by [hello]")

    def process_goodbye(self, sender):
        super().process_goodbye(sender)
        try:
            self.team.remove(sender)
            #self.number_of_peers -= 1
            self.lg.info(f"{self.ext_id}: process_goodbye: removed {sender} from team={self.team} by [goodbye]")
        except ValueError:
            self.lg.warning(f"{self.ext_id}: process_goodbye: failed to remove {sender} from team={self.team}")

    def process_unpacked_message(self, message, sender):
        chunk_number = message[ChunkStructure.CHUNK_NUMBER]
        self.lg.info(f"{self.ext_id}: process_unpacked_message: [{chunk_number}] <-- {sender}")

        if chunk_number >= 0:
            # We have received a chunk.
            chunk_data = message[ChunkStructure.CHUNK_DATA]
            origin = message[ChunkStructure.ORIGIN]
            chunk_data = message[ChunkStructure.CHUNK_DATA]
            self.lg.info(f"{self.ext_id}: process_unpacked_message: received chunk {chunk_number} from {sender} with origin {origin}")
            self.received_chunks += 1
            self.provide_CLR_feedback(sender)
            self.buffer_chunk(chunk_number = chunk_number, origin = origin, chunk_data = chunk_data, sender = sender)

        else:  # message[ChunkStructure.CHUNK_NUMBER] < 0
            if chunk_number == Messages.REQUEST:
                self.process_request(message[1], sender)
            elif chunk_number == Messages.PRUNE:
                self.process_prune(message[1], sender)
            elif chunk_number == Messages.HELLO:
                # if len(self.forward[self.id]) < self.max_degree:
                self.process_hello(sender)
            elif chunk_number == Messages.GOODBYE:
                self.process_goodbye(sender)
            else:
                self.lg.info("{self.ext_id}: process_unpacked_message: unexpected control chunk of index={chunk_number}")

        return (chunk_number, sender)

    def request_chunk(self, chunk_number, peer):
        #sys.stderr.write(f" R{self.ext_id}-{chunk_number}-{peer}"); sys.stderr.flush()
        msg = struct.pack("!ii", Messages.REQUEST, chunk_number)
        self.team_socket.sendto(msg, peer)

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
            #self.complain(self.buffer[chunk_position][ChunkStructure.CHUNK_NUMBER]) # If I'm a monitor
            self.number_of_lost_chunks += 1
            self.lg.warning(f"{self.ext_id}: play_chunk: lost chunk! {self.chunk_to_play} (number_of_lost_chunks={self.number_of_lost_chunks})")

            # The chunk "chunk_number" has not been received on time
            # and it is quite probable that is not going to change
            # this in the near future. The action here is to request
            # the lost chunk to one or more peers using a [request
            # <chunk_number>]. If after this, I start receiving
            # duplicate chunks, then a [prune <chunk_number>] should
            # be sent to those peers which send duplicates.

            # Request the chunk to the origin peer of the last received chunk.
            #i = self.prev_received_chunk
            #destination = self.buffer[i % self.buffer_size][ChunkStructure.ORIGIN]
            # while destination == None:
            #    i += 1
            #    destination = self.buffer[i % self.buffer_size][ChunkStructure.ORIGIN]
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

            if len(self.team) > 1:
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

        if __debug__:
            # Showing buffer
            buf = ""
            for i in self.buffer:
                if i[ChunkStructure.CHUNK_DATA] != b'L':
                    try:
                        _origin = self.team.index(i[ChunkStructure.ORIGIN])
                        buf += hash(_origin)
                    except ValueError:
                        buf += '-' # Peers do not exist in their team.
                        #peer_number = self.number_of_peers
                        #self.number_of_peers += 1
                    #buf += hash(peer_number)
                    #buf += '+'
                else:
                    buf += " "
            self.lg.debug(f"{self.ext_id}: play_chunk: buffer={buf}")

        #return self.player_connected
