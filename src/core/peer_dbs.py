"""
@package simulator
peer_dbs module
"""

import time
from threading import Thread
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import Socket_print as socket

class Peer_DBS(sim):

    MAX_CHUNK_DEBT = 128
    #NEIGHBORHOOD_DEGREE = 5
    
    def __init__(self, id):
        self.id = id
        self.played_chunk = 0 # Chunk currently played
        self.prev_received_chunk = 0 # ??
        self.buffer_size = 64 # Number of chunks in the buffer * 2
        self.chunks = [] # Buffer of chunks (circular queue)
        self.player_alive = True # While True, keeps the peer alive

        # ---Only for simulation purposes--- #
        self.losses = 0                      #
        self.played = 0                      #
        self.number_of_chunks_consumed = 0   #
        # ---------------------------------- #

        self.max_chunk_debt = self.MAX_CHUNK_DEBT
        self.peer_list = []  # Peers in the team (except you)
        self.debt = {}
        self.received_counter = 0
        self.number_of_monitors = 0
        self.receive_and_feed_counter = 0
        self.receive_and_feed_previous = ()
        self.debt_memory = 0
        self.waiting_for_goodbye = False
        self.modified_list = False
        self.number_of_peers = 0
        self.sendto_counter = 0
        self.ready_to_leave_the_team = False

        # A dictionary of lists of peers indexed by origin peers. For
        # each origin, we need a flooding list which says to which
        # peers must be forwarded each received chunk. In a
        # full-connected topology, there is only one list in the
        # dictionary (the rest can be considered as empty), with index
        # the owner (origin) peer, and with content the rest of peers
        # of the team. Notice that, to generate a full-connected team,
        # in a round, all chunks (one for each peer in the team except
        # the incoming peer) should be delivered directly to each
        # incoming peer from the origin peer.
        self.flooding_list = {}

        # During their life in the team (for example, when a peer
        # refuse to send data to it o simply to find better routes),
        # peers will request alternative routes for the chunks. To do
        # that, a [send once from <origin peer>] message will be sent
        # to at least one peer of the team. A peer that receive such
        # message will send (or not, depending on, for example, the
        # debt of the requesting peer) only one chunk from the origin
        # peer to the requesting peer. The requesting peer will send
        # to the first peer to send the chunk a [send from <origin
        # peer>] and both peers will be neighbors. To cancel this
        # message, a [not send from <origin peer>] must be used.

        self.RTTs = []
        # self.neighborhood_degree = self.NEIGHBORHOOD_DEGREE
        # self.neighborhood = []

        print(self.id, ": max_chunk_debt = ", self.MAX_CHUNK_DEBT)
        print(self.id, ": DBS initialized")

    def listen_to_the_team(self):
        self.team_socket = socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.team_socket.set_id(self.id)
        self.team_socket.bind(self.id+"_udp")

    def set_splitter(self, splitter):
        self.splitter = splitter

    def say_hello(self, peer):
        hello = (-1, "H", time.time())
        #self.sendto(hello, peer)
        self.team_socket.sendto(hello, peer)
        print(self.id, ": sent", hello, "to", peer)
        #(m, s) = self.recvfrom()
        #end = time.time()
        #self.RTTs.append((s, end-start))
        
    def say_goodbye(self, peer):
        goodbye = (-1, "G")
        #self.sendto(goodbye, peer)
        self.team_socket.sendto(goodbye, peer)
        print(self.id, ": sent", goodbye, "to", peer)

    def receive_buffer_size(self):
        #(self.buffer_size, sender) = self.recv()
        
        self.buffer_size = self.splitter_socket.recv(6)
        print(self.id, ": received buffer_size =", self.buffer_size, "from", self.splitter)

        # --- Only for simulation purposes ---------- #
        self.sender_of_chunks = [""]*self.buffer_size #
        # ------------------------------------------- #

    def receive_the_number_of_peers(self):
        #(self.number_of_monitors, sender) = self.recv()
        self.number_of_monitors = self.splitter_socket.recv(5)
        print(self.id, ": received number_of_monitors =", self.number_of_monitors, "from", self.splitter)
        #(self.number_of_peers, sender) = self.recv()
        self.number_of_peers = self.splitter_socket.recv(5)
        print(self.id, ": received number_of_peers =", self.number_of_peers, "from", self.splitter)

    # Thread(target=self.run).start()

    #ef set_neighborhood(self, peer):
    #    if len(self.neighborhood) < self.degree:
    #        self.neighborhood.append(peer)

    #def send_hellos(self, number_of_new_neighbors):
    def send_hellos(self):
        #print(self.id, ": number_of_new_neighbors =", number_of_new_neighbors)
        for peer in self.peer_list:
            self.say_hello(peer)
            print(self.id, ": hello sent to", peer)

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
            self.debt[peer] = 0         # Setting initial debts

    def receive_the_list_of_peers(self):
        #(self.peer_list, sender) = self.recv()[:]
        recv = self.splitter_socket.recv(5)
        self.peer_list = self.splitter_socket.recv(recv)
        print(self.id, ": received len(peer_list) =", len(self.peer_list), "from", self.splitter)

        # This line should be un commented (and the next one
        # commented) when DBS2 is fully active.
        #self.send_hellos(self.neighborhood_degree)
        #self.send_hellos(len(self.peer_list))

        # Default configuration for a fully connected overlay: only
        # one flooding list that says that the chunk received from the
        # splitter must be forwarded to the rest of the team
        self.flooding_list[self.id] = self.peer_list
        self.send_hellos()

    def connect_to_the_splitter(self):
        #hello = (-1, "P")
        #self.send(hello, self.splitter)
        #print(self.id, ": sent", hello, "to", self.splitter)
        self.splitter_socket = socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.splitter_socket.set_id(self.id)
        self.splitter_socket.bind(self.id+"_tcp")
        self.splitter_socket.connect(self.splitter)
        print("Connect to the splitter")
        
    def send_ready_for_receiving_chunks(self):
        ready = (-1, "R")
        #self.send(ready, self.splitter)
        self.splitter_socket.send(ready)
        print(self.id, ": sent", ready, "to", self.splitter)

    def send_chunk(self, peer):
        #self.sendto(self.receive_and_feed_previous, peer)
        self.team_socket.sendto(self.receive_and_feed_previous, peer)
        self.sendto_counter += 1

    def is_a_control_message(self, message):
        if message[0] == -1:
            return True
        else:
            return False

    def is_a_chunk(self, message):
        if message[0] > -1:
            return True
        return False 
        
    def process_message_2(self, message, sender):
        
        if is_a_chunk(message):

            # A chunk has been received

            self.received_chunks += 1
            chunk_number = message[0]

            if sender == self.splitter:

                # I'm the origin peer
                origin = self.id
                chunk = message[1]

                # Buffer the chunk
                self.chunks[chunk_number % self.buffer_size] = (chunk_number, origin, chunk)

            else:

                # I'm a relaying peer
                origin = message[1]
                chunk = message[2]

                if self.chunks[chunk_number % self.buffer_size][0] == chunk_number:
                    # Duplicate chunk: ignore it and prune path
                    self.send((-1, "X", origin), sender) # Hey <sender>, I don't want to receive more chunks from <origin>
                else:
                    # A new chunk has been received: buffer it
                    self.chunks[chunk_number % self.buffer_size] = (chunk_number, origin, chunk)

                if sender not in self.peer_list:
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print(self.id, ":", sender, "added by chunk", chunk_number)
                    print(self.id, ":", "peer_list =", self.peer_list)
                    # -------- For simulation purposes only ---------------------- #
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))          #
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender)) #
                    # ------------------------------------------------------------ #
                else:
                    self.debt[sender] -= 1

            # Flood the received chunk: 

        else:

            # A control message has been received
            if __debug__:
                print(self.id, ": control message received:", message)

            if message[1] == 'H': # Hello

                print(self.id, ": received", message, "from", sender)

                if sender not in self.peer_list:
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print(self.id, ":", sender, "added by [hello]")
                    print(self.id, ":", "peer_list =", self.peer_list)
                    # --- simulator ---------------------------------------------- #
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))          #
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender)) #
                    # ------------------------------------------------------------ #
                    
            elif message[1] == 'G': # Goodbye
                
                if sender in self.peer_list:
                    print(self.id, ": received goodbye from", sender)
                    try:
                        self.peer_list.remove(sender)
                        print(self.id, ":", sender, "removed from peer_list")
                    except:
                        print(self.id, ": failed to remove peer", sender, "from peer_list", self.peer_list)
                    print(self.id, ":", "peer_list =", self.peer_list)
                        
                    del self.debt[sender]
                else:
                    if (sender == self.splitter):
                        print(self.id, ": received goodbye from splitter")
                        self.waiting_for_goodbye = False

            return -1
                    
            # Configure flooding

            # By default, peers flood chunks to the rest of peers of
            # the team, excludind the origin peer. Peers must send
            # [prune <origin peer>] messages to those senders that
            # forwarded duplicate chunks, and send [not prune <origin
            # peer>] when the route for that origin peer fails.
            
            
            # For each origin peer, there is a list of peers that must
            # receive the chunk.
            
            
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

            self.received_chunks += 1
            if (sender == self.splitter):
                while((self.peer_index < len(self.peer_list)) and \
                      (self.peer_index > 0 or self.modified_list)):
                    peer = self.peer_list[self.peer_index]

                    self.send_chunk(peer)
                    self.debt[peer] += 1

                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        print(self.id, ":", peer, "removed by unsupportive (", str(self.debt[peer]), "lossess)")
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

            else:

                if sender not in self.peer_list:
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print(self.id, ":", sender, "added by chunk", chunk_number)
                    print(self.id, ":", "peer_list =", self.peer_list)
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
                    print(self.id,":",peer, "removed by unsupportive (" + str(self.debt[peer]) + " lossess)")
                    del self.debt[peer]
                    self.peer_list.remove(peer)
                    print(self.id, ":", "peer_list =", self.peer_list)
                    # self.neighborhood.remove(peer)
                    # print(self.id, ":", "neighborhood =", self.neighborhood)
                    # --- simulator ----------------------------------------- #
                    sim.FEEDBACK["DRAW"].put(("O","Edge","OUT",self.id,peer)) #
                    # ------------------------------------------------------- #

                #if __debug__:
                #    print(self.id, "-", str(self.receive_and_feed_previous[0]), "->", peer)

                self.peer_index += 1

            return chunk_number

        else:
            # A control chunk has been received
            if __debug__:
                print(self.id, ": control message received:", message)

            if message[1] == 'H': # Hello

                print(self.id, ": received", message, "from", sender)
                '''
                # Compute RTT of hello received from peer "sender"
                self.RTTs.append((sender, time.time() - message[2]))
                print(self.id, ": RTTs =", self.RTTs)
                '''
                if sender not in self.peer_list:
                    #self.sendto((-1, 'H', time.time()), sender)
                    self.team_socket.sendto((-1, 'H', time.time()), sender)
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print(self.id, ":", sender, "added by [hello]")
                    #self.distances[sender] = 1000
                    # --- simulator ---------------------------------------------- #
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))          #
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender)) #
                    # ------------------------------------------------------------ #
                    
            if message[1] == 'G': # Goodbye
                
                if sender in self.peer_list:
                    print(self.id, ": received goodbye from", sender)
                    try:
                        self.peer_list.remove(sender)
                        print(self.id, ":", sender, "removed from peer_list")
                    except:
                        print(self.id, ": failed to remove peer", sender, "from peer_list", self.peer_list)
                    print(self.id, ":", "peer_list =", self.peer_list)
                        
                    del self.debt[sender]
                else:
                    if (sender == self.splitter):
                        print(self.id, ": received goodbye from splitter")
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
        #content = self.recvfrom()
        #message = content[0]
        #sender = content[1]
        message, sender = self.team_socket.recvfrom(40)
        return self.process_message(message, sender)

    def polite_farewell(self):
        print(self.id, ": (see you later)")
        while (self.receive_and_feed_counter < len(self.peer_list)):
            #self.sendto(self.receive_and_feed_previous, self.peer_list[self.receive_and_feed_counter])
            self.team_socket.sendto(self.receive_and_feed_previous, self.peer_list[self.receive_and_feed_counter])
            self.team_socket.recvfrom(40)
            self.receive_and_feed_counter += 1

        for peer in self.peer_list:
            self.say_goodbye(peer)

        self.ready_to_leave_the_team = True
        print(self.id, ": ready to leave the team")

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

        print(self.id, ": position in the buffer of the first chunk to play", str(self.played_chunk))

        while (chunk_number < self.played_chunk or ((chunk_number - self.played_chunk) % self.buffer_size) < (self.buffer_size // 2)):
            chunk_number = self.process_next_message()
            # while (chunk_number < 0 or chunk_number < self.played_chunk):
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
        #if chunk_number % len(self.peer_list) != 0:
            #sim.LOCK.release()
        if self.chunks[chunk_number % self.buffer_size][1] == "C":
            self.played += 1
        else:
            self.losses += 1
            print(self.id, ": lost Chunk!", chunk_number)
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

    def am_i_a_monitor(self):
        return self.number_of_peers < self.number_of_monitors
