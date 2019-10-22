"""
@package simulator
peer_dbs2 module
"""

# Abstract class

# DBS2 (Data Broadcasting Set extension 2) layer, peer side.

# DBS2 extends the functionality of DBS considering that peers can
# receive the chunks indirectly, tracing multihop paths. Peers create
# such paths when chunks are lost.

import random
import struct
from .messages import Messages
from .chunk_structure import ChunkStructure
from .peer_dbs import Peer_DBS
import colorama
from .simulator_stuff import hash
import core.stderr as stderr
from .limits import Limits
from .ip_tools import IP_tools

class Peer_DBS2(Peer_DBS):

    def __init__(self):
        Peer_DBS.__init__(self)
        self.duplicates = {}

        # Peers (end-points) in the known team, which is formed by
        # those peers that has sent to this peer a chunk, directly or
        # indirectly. In DBS this structure is not necessary because
        # the list of peers of the peers plus the peer itself is the
        # team.
        self.team = []

    def set_optimization_horizon(self, optimization_horizon):
        self.optimization_horizon = optimization_horizon
        
    # Checks if the chunk with chunk_number was previously received.
    def is_duplicate(self, chunk_number):
        position = chunk_number % self.buffer_size
        duplicate = self.buffer[position][ChunkStructure.CHUNK_NUMBER] == chunk_number
        if __debug__:
            if duplicate:
                self.lg.debug(f"{self.ext_id}: duplicate {chunk_number} (the first one was originated by ({self.buffer[position][ChunkStructure.ORIGIN_ADDR]}, {self.buffer[position][ChunkStructure.ORIGIN_PORT]})")
        return duplicate

    # Add a new peer to the team list.
    def update_the_team(self, peer):
        self.lg.debug(f"{self.ext_id}: updating team with peer {peer}")
        self.team.append(peer)

    # The forwarding table indicates to which peers the received
    # chunks must be retransmitted. This method adds {destination} to the
    # list of peers forwarded for {origin}. If {origin} is new, a new
    # list is created. When {destination} is added, its pending table is
    # also created.
    def update_forward(self, origin, destination):
        if origin in self.forward:
            if destination not in self.forward[origin]:
                self.forward[origin].append(destination)
                #self.pending[destination] = [] OJJJJJJJJJJJJJJJJOOOOOOOOOOOOOOOOOOOOOOOOOOORRRRRRRRRRRRRRRRRRRRRRRRRRRR
                stderr.write("-")
            else:
                # {destination} already in {self.forward[origin]}
                stderr.write("+")
                pass
        else:
            # {origin} is not in self.forward
            self.forward[origin] = [destination]
            #self.pending[destination] = [] OJOJOOJOJOJOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
            #stderr.write(f"{self.ext_id}: origin={origin} destination={destination}")
        #assert origin in self.forward, f"{self.ext_id}: {origin} is not in {self.forward}"
        #assert destination in self.forward[origin], f"{self.ext_id}: {destination} not in {self.forward[origin]}"
        
        #stderr.write(f" [{len(self.forward)}]") # <---------------------
        #stderr.write(f"{self.forward}\n")

    def unpack_message(self, packet, sender):
        msg_format = "!i" + (len(packet)-4)*'s'
        chunk_number, *i_dont_know = struct.unpack(msg_format, packet)
        if chunk_number >= 0:
            self.received_chunks += 1
            chunk = list(struct.unpack(self.chunk_packet_format, packet))
            chunk[ChunkStructure.ORIGIN_ADDR] = IP_tools.int2ip(chunk[ChunkStructure.ORIGIN_ADDR])
            chunk[ChunkStructure.HOPS] += 1
            self.lg.debug(f"{self.ext_id}: received chunk {chunk} from {sender}")
            self.process_chunk(chunk, sender)
            self.send_chunks_to_the_next_neighbor()
        else:
            if chunk_number == Messages.HELLO:
                self.process_hello(sender)
            elif chunk_number == Messages.GOODBYE:
                self.process_goodbye(sender)
            elif chunk_number == Messages.REQUEST:
                self.process_request(chunk_number, sender)
            elif chunk_number == Messages.PRUNE:
                origin = struct.unpack('!iIi', packet)
                self.process_prune((IP_tools.int2ip(origin[1]), origin[2]), sender)
            else:
                stderr.write("{self.ext_id}: unexpected control chunk with code={chunk_number}")
        return (chunk_number, sender)

    def on_chunk_received_from_the_splitter(self, chunk):
        chunk_number = chunk[ChunkStructure.CHUNK_NUMBER]
        origin = chunk[ChunkStructure.ORIGIN_ADDR], chunk[ChunkStructure.ORIGIN_PORT]
        self.lg.debug(f"{self.ext_id}: processing chunk {chunk_number} with origin {origin} received from the splitter")
        self.buffer_chunk(chunk)

        # Increase inactivity and remove selfish neighbors.
        for neighbor in list(self.activity.keys()):
            self.activity[neighbor] -= 1
#        for _neighbor in list(self.activity):
            if self.activity[neighbor] < self.min_activity:
                del self.activity[neighbor]
                for neighbors in self.forward.values():
                    if neighbor in neighbors:
                        neighbors.remove(neighbor)
                # Habría que borrar las entradas de forward que
                #apuntan al selfish peer y los chunks pendientes.  del
                #self.pending[neighbor]

        # Can produce network congestion!
        #for neighbor in self.pending:
        #    self.send_chunks(neighbor)

        # Remove empty forwarding tables.
        #for _origin in list(self.forward.keys()):
        #    #if origin != self.public_endpoint:
        #    if len(self.forward[_origin]) == 0:
        #        del self.forward[_origin]

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

            max = 0
            for i in self.buffer:
                if i[ChunkStructure.CHUNK_DATA] != b'L':
                    hops = i[ChunkStructure.HOPS]
                    if hops > max:
                        max = hops
            stderr.write(f" {colorama.Back.RED}{colorama.Fore.BLACK}{max}{colorama.Style.RESET_ALL}")

        #if len(self.team) > 1:
        #    #peer = random.choice(self.team)
        #    peer = min(self.team, key=self.delta_inertia.get)
        #    #self.lg.info(f"{self.ext_id}: {peer} {self.team}")
        #    #peer = min(self.delta_inertia, key=self.delta_inertia.get)
        #    #stderr.write(f"{peer} {self.delta_inertia}\n")
        #    self.request_chunk(chunk_number, peer)
        #    #stderr.write(f" ->{peer}")
        #    if peer == self.ext_id[1]:
        #        stderr.write(f" ------------------------->hola!!!<---------------------")

    def on_chunk_received_from_a_peer(self, chunk, sender):
        chunk_number = chunk[ChunkStructure.CHUNK_NUMBER]
        origin = chunk[ChunkStructure.ORIGIN_ADDR], chunk[ChunkStructure.ORIGIN_PORT]
        self.lg.debug(f"{self.ext_id}: processing chunk {chunk_number} with origin {origin} received from the peer {sender}")
        
        #self.update_forward(origin, sender)
        if self.is_duplicate(chunk_number):
            try:
                self.duplicates[sender] += 1
            except KeyError:
                self.duplicates[sender] = 0
            if self.duplicates[sender] > 1000:
                self.request_prune(origin, sender)
                del self.duplicates[sender]
        else:
            self.buffer_chunk(chunk)

        # Extend the list of known peers checking if the origin of
        # the received chunk is new.
        if origin not in self.team:
            # In the optimization stage, the peer could request to
            # a neighbor a chunk that should be provided by the
            # splitter (the peer is the origin). If this happens,
            # the peer will receive chunks from neighbors for what
            # he is the origin (that is not good, but neither a
            # fatal error ... the peer will send a prunning
            # message to these neighbors), but the peer should not
            # be added to the team.
            if origin != self.public_endpoint:
                self.update_the_team(origin)

        try:
            self.activity[origin] += 1
        except KeyError:
            self.activity[origin] = 1

        #self.compute_deltas(chunk_number, sender)

    def process_chunk(self, chunk, sender):
        self.lg.debug(f"{self.ext_id}: processing chunk={chunk}")
        if sender == self.splitter:
            self.on_chunk_received_from_the_splitter(chunk)
        else:
            self.on_chunk_received_from_a_peer(chunk, sender)
        chunk_number = chunk[ChunkStructure.CHUNK_NUMBER]
        origin = chunk[ChunkStructure.ORIGIN_ADDR], chunk[ChunkStructure.ORIGIN_PORT]
        if origin in self.forward:
            self.update_pendings(origin, chunk_number)

    def request_chunk(self, chunk_number, peer):
        stderr.write(f" {colorama.Fore.CYAN}{self.ext_id[2]}/{chunk_number}/{peer[1]}{colorama.Style.RESET_ALL}")
        #stderr.write(f" R{self.ext_id}-{chunk_number}-{peer}")
        self.lg.debug(f"{self.ext_id}: sent [request {chunk_number}] to {peer}")
        msg = struct.pack("!ii", Messages.REQUEST, chunk_number)
        self.team_socket.sendto(msg, peer)

    # If a peer X receives [request chunk] from peer Z, X will
    # append Z to forward[chunk.origin], but only if Z is not the
    # origin of the requested chunk. This last thing can happen if
    # Z requests chunks that will be originated at itself.
    def process_request(self, chunk_number, sender):
        #stderr.write(f" {colorama.Back.CYAN}{colorama.Fore.BLACK}{chunk_number}/{sender[1]}{colorama.Style.RESET_ALL}")
        #stderr.write(f" {colorama.Fore.CYAN}{chunk_number}{colorama.Style.RESET_ALL}")
        self.lg.debug(f"{self.ext_id}: received [request {chunk_number}] from {sender}")
        #stderr.write(f" R{self.ext_id}/{chunk_number}/{sender}")
        position = chunk_number % self.buffer_size
        buffer_box = self.buffer[position]
        if buffer_box[ChunkStructure.CHUNK_DATA] != b'L':
            origin = buffer_box[ChunkStructure.ORIGIN_ADDR], buffer_box[ChunkStructure.ORIGIN_PORT] 
            if origin != sender:
                self.update_forward(origin, sender)
            else:
                self.lg.debug(f"{self.ext_id}: process_request: origin {origin} is the sender of the request")
        else:
            self.lg.debug(f"{self.ext_id}: process_request: chunk {chunk_number} is not in my buffer")

    # Pruning messages are sent when chunks are received more than
    # once.
    #def request_prune(self, chunk_number, peer):
    def request_prune(self, origin, peer):
        #stderr.write(f" {colorama.Back.CYAN}{colorama.Fore.BLACK}{self.ext_id[2]}/{chunk_number}/{peer[1]}{colorama.Style.RESET_ALL}")        
        #msg = struct.pack("!ii", Messages.PRUNE, chunk_number)
        #stderr.write(f" ---- {Messages.PRUNE} ---- {origin} ---- ")
#        stderr.write(f" (({Messages.PRUNE}, {IP_tools.ip2int(origin[0])}, {origin[1]}))")
        msg = struct.pack("!iIi", Messages.PRUNE, IP_tools.ip2int(origin[0]), origin[1])
        self.team_socket.sendto(msg, peer)
        #self.lg.debug(f"{self.ext_id}: [prune {chunk_number}] sent to {peer}")
        self.lg.debug(f"{self.ext_id}: sent [prune {origin}] to {peer}")

    # When a {peer} receives a [prune {chunk_number}{origin}], the {sender} is
    # requesting that {peer} stop sending chunks originated at
    # {self.buffer[chunk_number % self.buffer_size].origin}{origin}.
    #def process_prune(self, chunk_number, sender):
    def process_prune(self, origin, sender):
        stderr.write(f" {colorama.Back.CYAN}{colorama.Fore.BLACK}{self.ext_id[2]}/{origin[1]}/{sender[1]}{colorama.Style.RESET_ALL}")
        #stderr.write(f" {colorama.Fore.CYAN}{chunk_number}{colorama.Style.RESET_ALL}")
        #self.lg.debug(f"{self.ext_id}: received [prune {chunk_number}] from {sender}")
        self.lg.debug(f"{self.ext_id}: received [prune {origin}] from {sender}")

        def remove_sender(origin, sender):
            # Remove sender from forward[origin]
            assert sender in self.forward[origin], f"{self.ext_id}: {sender} is not in self.forward[{origin}]={self.forward[origin]}"
            self.forward[origin].remove(sender)
            self.lg.debug(f"{self.ext_id}: process_prune: sender={sender} has been removed from forward[{origin}]={self.forward[origin]}")

            # Remove the pending chunks to sender
            #self.pending[sender].clear()

        #position = chunk_number % self.buffer_size
        #buffer_box = self.buffer[position]
        
        # Notice that chunk "chunk_number" should be stored in the
        # buffer because it has been sent to the neighbor that is
        # requesting the prune.

        # Only complete prunning if I have the origin of the pruned chunk.
        #if buffer_box[ChunkStructure.CHUNK_NUMBER] == chunk_number:
            #origin = buffer_box[ChunkStructure.ORIGIN_ADDR], buffer_box[ChunkStructure.ORIGIN_PORT]
            #self.lg.debug(f"{self.ext_id}: process_prune: [prune {chunk_number}] received from {sender} for pruning origin={origin}")
        self.lg.debug(f"{self.ext_id}: process_prune: [prune {origin}] received from {sender}")
        if origin in self.forward:
            self.lg.debug(f"{self.ext_id}: process_prune: origin={origin} is in forward")
            if sender in self.forward[origin]:
                self.lg.debug(f"{self.ext_id}: process_prune: sender={sender} is in forward[{origin}]")
                remove_sender(origin, sender)
            else:
                self.lg.debug(f"{self.ext_id}: process_prune: sender={sender} is not in forward[{origin}]={self.forward[origin]}")
        else:
            self.lg.debug(f"{self.ext_id}: process_prune: origin={origin} is not in forward={self.forward}")
        #else:
            #self.lg.debug(f"{self.ext_id}: process_prune: chunk_number={chunk_number} is not in buffer ({self.buffer[position][ChunkStructure.CHUNK_NUMBER]}!={chunk_number})")

    def append_to_team(self, peer):
        assert peer != self.public_endpoint
        if peer not in self.team:
            self.team.append(peer)

    def process_hello(self, sender):
        self.lg.debug(f"{self.ext_id}: forward={self.forward}")
        self.lg.debug(f"{self.ext_id}: received [hello] from {sender}")
        # If a peer X receives [hello] from peer Z, X will
        # append Z to forward[X].
        #if self.public_endpoint in self.forward:
        assert self.public_endpoint in self.forward, f"{self.ext_id}: forward={self.forward} public_endpoint={self.public_endpoint}"
        if sender not in self.forward[self.public_endpoint]:
            self.forward[self.public_endpoint].append(sender)
            self.pending[sender] = []
        self.lg.debug(f"{self.ext_id}: forward={self.forward}")

        if sender not in self.team:
            if __debug__:
                if sender == self.public_endpoint:
                    self.lg.error(f"{self.ext_id}: appending myself to the team by [hello]")
            self.team.append(sender)
            self.lg.debug(f"{self.ext_id}: appended {sender} to team={self.team} by [hello]")
        self.delta_inertia[sender] = 0.0

    def process_goodbye(self, sender):
        Peer_DBS.process_goodbye(self, sender)
        try:
            self.team.remove(sender)
            #self.number_of_peers -= 1
            self.lg.debug(f"{self.ext_id}: process_goodbye: removed {sender} from team={self.team} by [goodbye]")
        except ValueError:
            self.lg.warning(f"{self.ext_id}: process_goodbye: failed to remove {sender} from team={self.team}")

    def ___process_unpacked_message(self, message, sender):
        chunk_number = message[ChunkStructure.CHUNK_NUMBER]

        if chunk_number >= 0:
            # We have received a chunk.
            self.lg.debug(f"{self.ext_id}: received chunk {message} from {sender}")
            self.received_chunks += 1
            self.process_chunk(message, sender)
            self.send_chunks_to_the_next_neighbor()
        else:  # message[ChunkStructure.CHUNK_NUMBER] < 0
            stderr.write(f" <<{chunk_number}>>")
            if chunk_number == Messages.REQUEST:
                self.process_request(message[1], sender)
            elif chunk_number == Messages.PRUNE:
                stderr.write(f" ==== {message} ====")
                self.process_prune((IP_tools.int2ip(message[1]), message[2]), sender)
            elif chunk_number == Messages.HELLO:
                self.process_hello(sender)
            elif chunk_number == Messages.GOODBYE:
                self.process_goodbye(sender)
            else:
                stderr.write("{self.ext_id}: process_unpacked_message: unexpected control chunk of index={chunk_number}")
        return (chunk_number, sender)

    def play_chunk(self, chunk_number):
        optimized_chunk = (chunk_number + self.optimization_horizon) % Limits.MAX_CHUNK_NUMBER
        buffer_box = self.buffer[optimized_chunk % self.buffer_size]
        if buffer_box[ChunkStructure.CHUNK_DATA] == b'L':
            if len(self.team)>1:
                peer = random.choice(self.team)
                #peer = min(self.team, key=self.delta_inertia.get)
                self.request_chunk(optimized_chunk, peer)

        buffer_box = self.buffer[chunk_number % self.buffer_size]
        self.lg.debug(f"{self.ext_id}: chunk={chunk_number} hops={buffer_box[ChunkStructure.HOPS]}")
        if buffer_box[ChunkStructure.CHUNK_DATA] == b'L':
            # The cell in the buffer is empty.
            self.complain(chunk_number) # Only monitors
            #self.complain(self.buffer[chunk_position][ChunkStructure.CHUNK_NUMBER]) # If I'm a monitor
            self.number_of_lost_chunks_in_this_round += 1
            self.lg.debug(f"{self.ext_id}: lost chunk! {self.chunk_to_play} (number_of_lost_chunks={self.number_of_lost_chunks_in_this_round})")
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

            #if self.ext_id[0] == '000':
                #stderr.write(f" {self.team}")
            if len(self.team) > 1:
                peer = random.choice(self.team)
                #peer = min(self.team, key=self.delta_inertia.get)
                #peer = min(self.delta_inertia, key=self.delta_inertia.get)
                #stderr.write(f"{peer} {self.delta_inertia}\n")
                self.request_chunk(chunk_number, peer)
                #stderr.write(f" ->{peer}")
                if peer == self.ext_id[1]:
                    stderr.write(f" ------------------------->hola!!!<---------------------")

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
        else:
            # Only the data will be empty in order to remember things ...
            self.buffer[chunk_number % self.buffer_size] = self.clear_entry_in_buffer(buffer_box)
            self.played += 1

        self.number_of_chunks_consumed += 1
        if __debug__:
            #stderr.write(f" {len(self.forward)}")
            buf = ""
            for i in self.buffer:
                if i[ChunkStructure.CHUNK_DATA] != b'L':
                    try:
                        _origin = list(self.team).index((i[ChunkStructure.ORIGIN_ADDR],i[ChunkStructure.ORIGIN_PORT]))
                        buf += hash(_origin)
                    except ValueError:
                        buf += '-'  # Does not exist in their forwarding table.
                else:
                    buf += " "
            self.lg.debug(f"{self.ext_id}: buffer={buf}")


