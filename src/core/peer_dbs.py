"""
@package simulator
peer_dbs module
"""

# DBS layer

# Peers send [request <chunk>] (where <chunk> is a chunk index) to a
# random peer (between the peers that have a small debt) when <chunk>
# is missing while the playback. If a peer receive a [request
# <chunk>], it will continue sending to the sender of this message
# those chunks that come from the origin peer which sent the chunk
# <chunk>, until the requesting peer sends a [prune <origin>].

# During their life in the team (for example, when a peer refuse to
# send data to it o simply to find better routes), peers will request
# alternative routes for the chunks. To do that, a [send once from
# <origin peer>] message will be sent to at least one peer of the
# team. A peer that receive such message will send (or not, depending
# on, for example, the debt of the requesting peer) only one chunk
# from the origin peer to the requesting peer. The requesting peer
# will send to the first peer to send the chunk a [send from <origin
# peer>] and both peers will be neighbors. To cancel this message, a
# [prune <origin>] must be used.

from threading import Thread
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import Socket_print as socket
from .simulator_stuff import lg
import sys

class Peer_DBS(sim):

    # This not makes sense in DBS2?
    MAX_CHUNK_DEBT = 128
    
    def __init__(self, id):
        self.id = id
        self.played_chunk = 0 #  Chunk currently played
        self.prev_received_chunk = 0 #  ??
        self.buffer_size = 64 #  Number of chunks in the buffer * 2
        self.chunks = [] #  Buffer of chunks (used as a circular queue)
        self.player_alive = True #  While True, keeps the peer alive

        # ---Only for simulation purposes--- #
        self.losses = 0                      #
        self.played = 0                      #
        self.number_of_chunks_consumed = 0   #
        self.chunks_before_leave = 0         #
        # ---------------------------------- #

        self.max_chunk_debt = self.MAX_CHUNK_DEBT
        self.peer_list = []  # Peers in the team (except you)
        self.debt = {}
        self.received_chunks = 0
        self.number_of_monitors = 0
        self.receive_and_feed_counter = 0
        self.receive_and_feed_previous = ()
        self.debt_memory = 0
        self.waiting_for_goodbye = False
        self.modified_list = False
        self.number_of_peers = 0
        self.sendto_counter = 0
        self.ready_to_leave_the_team = False

        # A dictionary indexed by origins and that contains list of
        # peers. By default, all peers will have one entry for those
        # chunks received from the splitter (for which it is the
        # origin) and that must forward to the rest of the team.
        self.flooding_list = {}

        #self.RTTs = []
        # self.neighborhood_degree = self.NEIGHBORHOOD_DEGREE
        # self.neighborhood = []

        #print(self.id, ": max_chunk_debt = ", self.MAX_CHUNK_DEBT)
        lg.info("{}: DBS initialized".format(self.id))

    def listen_to_the_team(self):
        self.team_socket = socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.team_socket.set_id(self.id)
        self.team_socket.bind(self.id+"_udp")

    def set_splitter(self, splitter):
        self.splitter = splitter

    def say_hello(self, peer):
        hello = (-1, "H")
        self.team_socket.sendto("is", hello, peer)

    def say_goodbye(self, peer):
        goodbye = (-1, "G")
        self.team_socket.sendto("is", goodbye, peer)

    def receive_buffer_size(self):     
        self.buffer_size = self.splitter_socket.recv("H")
        lg.info("{}: received buffer_size = {} from {}".format(self.id, self.buffer_size, self.splitter))
        # --- Only for simulation purposes ---------- #
        self.sender_of_chunks = [""]*self.buffer_size #
        # ------------------------------------------- #

    def receive_the_number_of_peers(self):
        self.number_of_monitors = self.splitter_socket.recv("H")
        lg.info("{}: received number_of_monitors = {} from {}".format(self.id, self.number_of_monitors, self.splitter))
        self.number_of_peers = self.splitter_socket.recv("H")
        lg.info("{}: received number_of_peers = {} from {}".format(self.id, self.number_of_peers, self.splitter))

    def send_hellos(self):
        for peer in self.peer_list:
            #self.say_hello(peer)
            #print(self.id, ": hello sent to", peer)
            pass

        '''
        # Ojo, esto no se puede llamar desde process_message porque tarda en regresar ...
        # Computing RTTs ("run" method must be running in a thread)
        #while len(self.RTTs) < len(self.peer_list) - len(self.neighborhood):
        #    time.sleep(1)

        # Determining neighborhood
        sorted_RTTs = sorted(self.RTTs, key=lambda x: x[1])
        print(self.id, ": RTTs =", sorted_RTTs)
        #for p in range(min(len(sorted_RTTs), self.neighborhood_degree)):
        #for p in range(min(len(sorted_RTTs), number_of_new_neighbors)):
        for p in range(min(len(sorted_RTTs), len(self.peer_list))):
            if sorted_RTTs[p][0] not in self.neighborhood:
                self.neighborhood.append(sorted_RTTs[p][0])
        print(self.id, ": neighborhood =", self.neighborhood)
        '''
        #for peer in self.neighborhood:
        for peer in self.peer_list:
            '''self.distances[peer] = 1    # Setting initial distances'''
            #self.sendto((-1, 'X', self.distances), peer)
            #self.debt[peer] = 0         # Setting initial debts
            pass

    def receive_the_list_of_peers(self):
        peers_pending_of_reception = self.number_of_peers
        while peers_pending_of_reception > 0:
            peer = self.splitter_socket.recv("6s")
            #self.peer_list.append(peer)
            #self.debt[peer] = 0
            self.say_hello(peer)
            lg.info("{}: sent [forward chunk originated at {}]  sent to {}".format(self.id, peer))

            peers_pending_of_reception -= 1

        lg.info("{} : received len(peer_list) = {} from {}".format(self.id, len(self.peer_list), self.splitter))

        # Default configuration for fully connected overlays: the rest
        # of the team will receive only those chunks received from the
        # splitter.

        self.flooding_list[self.id] = self.peer_list

    def connect_to_the_splitter(self):
        self.splitter_socket = socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.splitter_socket.set_id(self.id)
        self.splitter_socket.bind(self.id+"_tcp")
        try:
            self.splitter_socket.connect(self.splitter)
        except ConnectionRefusedError as e:
            sys.stderr.write("Error en Peer {}".format(self.id))
            sys.stderr.write("{}".format(e))
            raise

        lg.info("{}: connected to the splitter".format(self.id))

    def send_ready_for_receiving_chunks(self):
        ready = ("R")
        self.splitter_socket.send("s", ready)
        lg.info("{}: sent {} to {}".format(self.id, ready, self.splitter))

    def send_chunk(self, peer):
        self.team_socket.sendto("is", self.receive_and_feed_previous, peer)
        self.sendto_counter += 1 # For informative issues

    def is_a_control_message(self, message):
        if message[0] == -1:
            return True
        else:
            return False

    def is_a_chunk(self, message):
        if message[0] > -1:
            return True
        return False 

    def process_message2(self, message, sender):

        # ----- Check if new round for peer (simulation purposes) ------------- #
        if not self.is_a_control_message(message) and sender == self.splitter:  #
            if self.played > 0 and self.played >= len(self.peer_list):          #
                clr = self.losses/self.played                                   #
                sim.FEEDBACK["DRAW"].put(("CLR", self.id, clr))                 #
                self.losses = 0                                                 #
                self.played = 0                                                 #
        # --------------------------------------------------------------------- #

        if (message[0] < 0):

            if message[1] == 'H': # [hello]

                lg.info("{}: received [hello] from {}".format(self.id, sender))

                if sender not in self.peer_list:

                    # Insert sender to the list of peers
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    lg.debug("{}: inserted {} by [hello]".format(self.id, sender))  

                    # --- simulator ---------------------------------------------- #
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))          #
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender)) #
                    # ------------------------------------------------------------ #

            elif message[1] == 'G': # [goodbye]

                lg.info("{}: received [goodbye] from {}".format(self.id, sender))
                
                if sender in self.peer_list:
                    
                    try:
                        self.peer_list.remove(sender)
                        lg.error("{}: {} removed from peer_list".format(self.id, sender))
                    except ValueError:
                        lg.error("{}: : failed to remove peer {} from peer_list {}".format(sef.id, sender, self.peer_list))
                    lg.info("{}: peer_list = {}".format(self.id, self.peer_list))    
                    del self.debt[sender]
                    
                else: # sender is not in peer_list
                    
                    if (sender == self.splitter):
                        lg.info("{}: received [goodbye] from splitter".format(self.id))
                        self.waiting_for_goodbye = False

            elif message[1] == 'F': # [forward]

                origin = message[2]
                lg.info("{}: received [Forward chunks from origin {}] from {}".format(self.id, origin, sender))

                # When arriving, all peers request to the rest of
                # peers of the team those chunks whose source is the
                # peer which receives the request. So in the
                # forwarding list of each peer will be an entry
                # indexed by <self.id> (the origin peer referenced by
                # the incoming peer) what will point to the list of
                # peers of the team whose request has arrived. Other
                # nodes in the forwarding list will be generated for
                # other peers that request the forwarding of the
                # corresponding source.
        
                if sender not in self.forward[origin]:

                    # Insert sender to the list of peers
                    self.debt[sender] = 0
                    self.forward[origin].append(sender)
                    lg.info("{}: inserted {} by [Forward chunks from origin {}]".format(self.id, sender, origin))
                    
                    # --- simulator ---------------------------------------------- #
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))          #
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender)) #
                    # ------------------------------------------------------------ #
                    
            elif message[1] == 'P': # [prune]

                lg.info("{}: received [prune chunks from origin {}] from {}".format(self.id, message[2], sender))

        else: # message[0] >= 0
                    
            # chunk -> buffer[chunk_number]
            chunk_number = message[0]
            chunk = message[1]
            self.received_chunks += 1
            self.chunks[chunk_number % self.buffer_size] = (chunk_number, chunk)

            # --- for simulation purposes only ---------------------------------------------- #
            self.sender_of_chunks[chunk_number % self.buffer_size] = sender                   #
                                                                                              #
            chunks = ""                                                                       #
            for n, c in self.chunks:                                                          #
                chunks += c                                                                   #
                if c == "L":                                                                  #
                    self.sender_of_chunks[n % self.buffer_size] = ""                          #
                                                                                              #
            sim.FEEDBACK["DRAW"].put(("B", self.id, chunks,":".join(self.sender_of_chunks)))  #
            # ------------------------------------------------------------------------------- #

            # For example, if in the team there are 3 peers A, B and
            # C, and a new incoming peer D wants to join, D will sent
            # to A a [Forward A], to B a [Forward B] and to C a
            # [Forward C]. In the forwarding list of A, D will be
            # appended to the entry forward[A], in B, forward[B] will
            # add D, and in C, forward[C] will add D.

            # In overlays where all peers are directly connected with
            # the rest (the degree of all peers is N-1 where N is the
            # number of peers in the team) and no
            # alternative/redundant path are defined, the forwarding
            # list of a peer X will have only the entry forward[X]
            # that will point to the rest of peers of the team. When a
            # peer X requests to peer Y to forward chunks from source
            # Z, Y will append X to forward[Z]. So, Y will have at
            # least two entries in its forwarding list: forward[Y]
            # (with the rest of peers of the team) and forward[Z]
            # (with at least X).

            # When a peer X receives a chunk (number) C with source Y,
            # for each node E of forward[Y], X performs
            # pending[E].append(C).

            # When peer X receives a chunk, X selects the next entry E
            # of pending, sends the chunk C indicated by pending[E] to
            # E, and removes C from pending[E]. If in pending[E] there
            # are more than one chunk, all chunks are sent in a
            # burst. In the first iteration, E is selected at random.
            
            # -----------------------

            # The source of the received chunks from the splitter is
            # the receiver of the chunk. The source of a received
            # chunk from a peer will be that peer or a different one.

            # When a chunk is received by peer X from source Y
            # (remember that Y==X if the sender is S), it will be sent
            # to the next entry of <forward[Y]>.
            
            # Received chunks can came from the splitter S or from a
            # peer X. If the sender is X, the receiver peer Y (me)
            # will forward one or more chunks to different peers,
            # those referenced by <forward[X]>. These chunks are sent
            # in burst mode. Notice that the received chunk is sent
            # first to a peer that requested the forwarding when
            # arrived to the team and next are sent to peers which
            # requested it later.


            The chunks sent to Z
            # are all those received by Y from S, that has not been
            # sent to Z previously, and the received chunks from other
            # peers and that been previously requested by Z.
            
            # Received chunks can came from the splitter and from
            # another peer. If the sender is the splitter, the
            # received chunk will be sent to a (different) peer of the
            # list of peers. If the sender is a peer, the received
            # chunk could be sent also to a different peer, if it
            # requested it.

            # For each received chunk, a list of destinations is
            # defined. If the chunk has been received from the
            # splitter, the destinations are all the peers of the list
            # of peers. If the chunk has been received from a peer,
            # because I (peer) requested it, I have to check if I have
            # to forward the chunk to other peer, because it requested
            # it.

            # For each received chunk, we will go through the next entry of the forwarding list which is indexed by peers identificators. Each entry of such list will have at least one destination (
            
            if (sender == self.splitter):

                # Add the received chunk to the list of pending forwardings
                for peer in self.peer_list:
                    self.pending[peer].append(chunk_number) # The chunk itself is already in the buffer
                    # After we will forward the received chunk to th
                    
                origin = self.id
                    
            else: # sender != self.splitter

                if origin is in self.relay:

                    # We have received a chunk (from a peer) which (the chunk) must be forwarded
                
                if sender not in self.peer_list:

                    # Insert sender to the list of peers & establish its debt to 0
                    self.peer_list.append(sender)
                    lg.info("{}: {} added by chunk".format(sender, chunk_number))
                    lg.debug("{}: peer_list =".format(self.id, self.peer_list))
                    self.debt[sender] = 0

                    # -------- For simulation purposes only ---------------------- #
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))          #
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender)) #
                    # ------------------------------------------------------------ #

                else: # sender is in list of peers

                    # Decrement sender's debt
                    self.debt[sender] -= 1

    def process_message(self, message, sender):

        # ----- Check if new round for peer (simulation purposes) ------------- #
        if not self.is_a_control_message(message) and sender == self.splitter:  #
            if self.played > 0 and self.played >= len(self.peer_list):          #
                clr = self.losses/self.played                                   #
                sim.FEEDBACK["DRAW"].put(("CLR", self.id, clr))                 #
                self.losses = 0                                                 #
                self.played = 0                                                 #
        # --------------------------------------------------------------------- #

        if (message[0] >= 0):

            # A chunk has been received
            
            chunk_number = message[0]
            chunk = message[1]
            self.received_chunks += 1
            
            self.chunks[chunk_number % self.buffer_size] = (chunk_number, chunk)

            # --- for simulation purposes only ---------------------------------------------- #
            self.sender_of_chunks[chunk_number % self.buffer_size] = sender                   #
                                                                                              #
            chunks = ""                                                                       #
            for n, c in self.chunks:                                                          #
                chunks += c                                                                   #
                if c == "L":                                                                  #
                    self.sender_of_chunks[n % self.buffer_size] = ""                          #
                                                                                              #
            sim.FEEDBACK["DRAW"].put(("B", self.id, chunks,":".join(self.sender_of_chunks)))  #
            # ------------------------------------------------------------------------------- #

            #  For simulation purposes ----------------------------- #
            if (self.received_chunks >= self.chunks_before_leave):   #
                self.player_alive = False                            #
            #  ----------------------------------------------------- #

            if (sender == self.splitter):
                while((self.peer_index < len(self.peer_list)) and \
                      (self.peer_index > 0 or self.modified_list)):
                    peer = self.peer_list[self.peer_index]

                    self.send_chunk(peer)
                    self.debt[peer] += 1

                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        lg.info("{}: {} removed by unsupportive ({} losses)".format(self.id, peer, str(self.debt[peer])))
                        del self.debt[peer]
                        self.peer_list.remove(peer)
                        # --- simulator --------------------------------------------- #
                        sim.FEEDBACK["DRAW"].put(("O", "Edge", "OUT", self.id, peer)) #
                        # ----------------------------------------------------------- #
                    else:
                        self.peer_index += 1

                # Modifying the first chunk to play (it increases the delay)
                #if (not self.receive_and_feed_previous):
                    #self.played_chunk = message[0]
                    #print(self.id,"First chunk to play modified", str(self.played_chunk))

                self.modified_list = False
                self.peer_index = 0
                self.receive_and_feed_previous = message

            else: # sender != self.splitter

                if sender not in self.peer_list:
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    lg.info("{}: {} added by chunk {}".format(self.id, sender, chunk_number))   
                    lg.info("{}: peer_list = {}".format(self.id, self.peer_list))
                    # -------- For simulation purposes only ---------------------- #
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))          #
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender)) #
                    # ------------------------------------------------------------ #
                else:
                    self.debt[sender] -= 1
                '''
                if self.distances[sender] > 1:
                    self.distances[sender] = 1
                    for peer in self.neighborhood:
                        self.sendto((-1, 'X', self.distances), peer)
                
                if sender not in self.neighborhood:
                    self.neighborhood.append(sender)
                    print(self.id, ":", "neighborhood =", self.neighborhood)
                '''
            if (self.peer_index < len(self.peer_list) and (self.receive_and_feed_previous)):
                peer = self.peer_list[self.peer_index]

                self.send_chunk(peer)
                self.debt[peer] += 1

                if (self.debt[peer] > self.MAX_CHUNK_DEBT):
                    lg.info("{}: {} removed by unsupportive ({} losses".format(self.id, peer, self.debt[peer]))
                    del self.debt[peer]
                    self.peer_list.remove(peer)
                    lg.info("{}: peer_list = {}".format(self.id, self.peer_list))

                    # self.neighborhood.remove(peer)
                    # print(self.id, ":", "neighborhood =", self.neighborhood)
                    # --- simulator ----------------------------------------- #
                    sim.FEEDBACK["DRAW"].put(("O","Edge","OUT",self.id,peer)) #
                    # ------------------------------------------------------- #

                self.peer_index += 1

            return chunk_number

        else:
            # A control chunk has been received

            if message[1] == 'H': # [hello]

                lg.info("{}: received [hello] from".format(self.id, sender))

                '''
                # Compute RTT of hello received from peer "sender"
                self.RTTs.append((sender, time.time() - message[2]))
                print(self.id, ": RTTs =", self.RTTs)
                '''
                if sender not in self.peer_list:
                    #self.sendto((-1, 'H', time.time()), sender)
                    #self.team_socket.sendto((-1, 'H', time.time()), sender)
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    lg.info("{}: inserted {} by [hello]".format(self.id, sender))

                    #self.distances[sender] = 1000
                    # --- simulator ---------------------------------------------- #
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))          #
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender)) #
                    # ------------------------------------------------------------ #
                    
            elif message[1] == 'G': # Goodbye
                
                lg.info("{}: received [goodbye] from".format(self.id, sender))
                
                if sender in self.peer_list:
                    try:
                        self.peer_list.remove(sender)
                        lg.error("{}: {} removed from peer_list".format(self.id, sender))
                    except ValueError:
                        lg.error("{}: : failed to remove peer {} from peer_list {}".format(sef.id, sender, self.peer_list))
                    lg.info("{}: peer_list = {}".format(self.id, self.peer_list))    

                    del self.debt[sender]
                else:
                    if (sender == self.splitter):
                        lg.info("{}: received [goodbye] from splitter".format(self.id))
                        self.waiting_for_goodbye = False

            '''
            if message[1] == 'X': # Routing information
                found_shorter_distance = False
                distances_to = message[2]
                print(self.id, ": current distances", self.distances)
                print(self.id, ": received distances", distances_to, "from", sender)
                for peer in distances_to:
                    print("distances:", distances_to[peer], self.distances[sender], self.distances[peer])
                    if distances_to[peer] + self.distances[sender] < self.distances[peer]:
                        self.distances[peer] = distances_to[peer] + self.distances[sender]
                        found_shorter_distance = True
                        print("distances: found shorter distance for peer", peer)
                print(self.id, ": computed distances", self.distances)
                if found_shorter_distance:
                    for peer in self.neighborhood:
                        self.sendto((-1, 'X', self.distances), peer)
            '''     
            return -1

    def process_next_message(self):
        message, sender = self.team_socket.recvfrom("is")
        return self.process_message(message, sender)

    def polite_farewell(self):
        lg.info("{}: (see you later)".format(self.id))
        while (self.receive_and_feed_counter < len(self.peer_list)):
            self.send_chunk(self.peer_list[self.receive_and_feed_counter])
            self.team_socket.recvfrom("is")
            self.receive_and_feed_counter += 1

        for peer in self.peer_list:
            self.say_goodbye(peer)

        self.ready_to_leave_the_team = True
        lg.info("{}: ready to leave the team".format(self.id))

    def buffer_data(self):
        self.peer_index = 0
        self.receive_and_feed_previous = ()
        self.sendto_counter = 0
        self.debt_memory = 1 << self.MAX_CHUNK_DEBT
        self.waiting_for_goodbye = True
        for i in range(self.buffer_size):
            self.chunks.append((i, "L"))

        chunk_number = self.process_next_message()

        while(chunk_number < 0):
            chunk_number = self.process_next_message()

        self.played_chunk = chunk_number

        lg.info("{}: position in the buffer of the first chunk to play".format(self.id, self.played_chunk))
        
        while (chunk_number < self.played_chunk or ((chunk_number - self.played_chunk) % self.buffer_size) < (self.buffer_size // 2)):
            chunk_number = self.process_next_message()
            while (chunk_number < self.played_chunk):
                chunk_number = self.process_next_message()
        self.prev_received_chunk = chunk_number

    def play_next_chunks(self, last_received_chunk):
        for i in range(last_received_chunk - self.prev_received_chunk):
            self.player_alive = self.play_chunk(self.played_chunk)
            self.chunks[self.played_chunk % self.buffer_size] = (self.played_chunk, "L")
            self.played_chunk = (self.played_chunk + 1) % Common.MAX_CHUNK_NUMBER
        if ((self.prev_received_chunk % Common.MAX_CHUNK_NUMBER) < last_received_chunk):
            self.prev_received_chunk = last_received_chunk

    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number % self.buffer_size][1] == "C":
            self.played += 1
        else:
            self.losses += 1
            lg.info("{}: lost chunk! {}".format(self.id, chunk_number))
        self.number_of_chunks_consumed += 1
        return self.player_alive

    def keep_the_buffer_full(self):
        last_received_chunk = self.process_next_message()
        while (last_received_chunk < 0):
            last_received_chunk = self.process_next_message()

        self.play_next_chunks(last_received_chunk)

    def start(self):
        Thread(target=self.run).start()

    def run(self):
        while (self.player_alive or self.waiting_for_goodbye):
            self.keep_the_buffer_full()
            if not self.player_alive:
                self.say_goodbye(self.splitter)
        self.polite_farewell()
        self.team_socket.close()

    def am_i_a_monitor(self):
        return self.number_of_peers < self.number_of_monitors
