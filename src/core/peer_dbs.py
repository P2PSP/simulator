"""
@package simulator
peer_dbs module
"""

import time
from threading import Thread
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import Socket_queue


class Peer_DBS(sim, Socket_queue):
    MAX_CHUNK_DEBT = 128
    NEIGHBORHOOD_DEGREE = 5
    
    def __init__(self, id):
        self.id = id
        self.played_chunk = 0
        self.prev_received_chunk = 0
        self.buffer_size = 64
        self.player_alive = True
        self.chunks = []

        # ---Only for simulation purposes--- #
        self.losses = 0                      #
        self.played = 0                      #
        self.number_of_chunks_consumed = 0   #
        # ---------------------------------- #

        self.max_chunk_debt = self.MAX_CHUNK_DEBT
        self.peer_list = []
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

        self.RTTs = []
        self.neighborhood_degree = self.NEIGHBORHOOD_DEGREE
        self.neighborhood = []
        
        print(self.id, ": max_chunk_debt = ", self.MAX_CHUNK_DEBT)
        print(self.id, ": DBS initialized")

    def set_splitter(self, splitter):
        self.splitter = splitter

    def say_hello(self, peer):
        hello = (-1, "H", time.time())
        self.sendto(hello, peer)
        print(self.id, ": sent", hello, "to", peer)
        #(m, s) = self.recvfrom()
        #end = time.time()
        #self.RTTs.append((s, end-start))
        
    def say_goodbye(self, peer):
        goodbye = (-1, "G")
        self.sendto(goodbye, peer)
        print(self.id, ": sent", goodbye, "to", peer)

    def receive_buffer_size(self):
        (self.buffer_size, sender) = self.recv()
        print(self.id, ": received buffer_size =", self.buffer_size, "from", sender)

        # --- Only for simulation purposes ---------- #
        self.sender_of_chunks = [""]*self.buffer_size #
        # ------------------------------------------- #

    def receive_the_number_of_peers(self):
        (self.number_of_monitors, sender) = self.recv()
        print(self.id, ": received number_of_monitors =", self.number_of_monitors, "from", sender)
        (self.number_of_peers, sender) = self.recv()
        print(self.id, ": received number_of_peers =", self.number_of_peers, "from", sender)

    # Thread(target=self.run).start()

    #ef set_neighborhood(self, peer):
    #    if len(self.neighborhood) < self.degree:
    #        self.neighborhood.append(peer)

    def send_hellos(self, number_of_new_neighbors):
        print(self.id, ": number_of_new_neighbors =", number_of_new_neighbors)
        for peer in self.peer_list:
            if peer not in self.neighborhood: # You don't need to compute RTT with neighbors
                self.say_hello(peer)
        print(self.id, ":", self.peer_list)

        # Ojo, esto no se puede llamar desde process_message porque tarda en regresar ...
        # Computing RTTs ("run" method must be running in a thread)
        #while len(self.RTTs) < len(self.peer_list) - len(self.neighborhood):
        #    time.sleep(1)

        # Determining neighborhood
        sorted_RTTs = sorted(self.RTTs, key=lambda x: x[1])
        print(self.id, ": RTTs =", sorted_RTTs)
        for p in range(min(len(sorted_RTTs), number_of_new_neighbors)):
            if sorted_RTTs[p][0] not in self.neighborhood:
                self.neighborhood.append(sorted_RTTs[p][0])
        print(self.id, ": neighborhood =", self.neighborhood)
    
    def receive_the_list_of_peers(self):
        (self.peer_list, sender) = self.recv()[:]
        print(self.id, ": received len(peer_list) =", len(self.peer_list), "from", sender)
        self.send_hellos(self.neighborhood_degree)
        for peer in self.peer_list:
            self.debt[peer] = 0            
        
    def connect_to_the_splitter(self):
        hello = (-1, "P")
        self.send(hello, self.splitter)
        print(self.id, ": sent", hello, "to", self.splitter)

    def send_ready_for_receiving_chunks(self):
        ready = (-1, "R")
        self.send(ready, self.splitter)
        print(self.id, ": sent", ready, "to", self.splitter)

    def send_chunk(self, peer):
        self.sendto(self.receive_and_feed_previous, peer)
        self.sendto_counter += 1

    def is_a_control_message(self, message):
        if message[0] == -1:
            return True
        else:
            return False

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

            self.received_counter += 1
            if (sender == self.splitter):
                while((self.receive_and_feed_counter < len(self.peer_list)) and \
                      (self.receive_and_feed_counter > 0 or self.modified_list)):
                    peer = self.peer_list[self.receive_and_feed_counter]

                    self.send_chunk(peer)
                    self.debt[peer] += 1

                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        print(self.id, ":", peer, "removed by unsupportive (", str(self.debt[peer]), "lossess)")
                        del self.debt[peer]
                        self.peer_list.remove(peer)
                        # --- simulator --------------------------------------------- #
                        sim.FEEDBACK["DRAW"].put(("O", "Edge", "OUT", self.id, peer)) #
                        # ----------------------------------------------------------- #

                    self.receive_and_feed_counter += 1

                # Modifying the first chunk to play (it increases the delay)
                #if (not self.receive_and_feed_previous):
                    #self.played_chunk = message[0]
                    #print(self.id,"First chunk to play modified", str(self.played_chunk))

                self.modified_list = False
                self.receive_and_feed_counter = 0
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

                if sender not in self.neighborhood:
                    self.neighborhood.append(sender)
                    print(self.id, ":", "neighborhood =", self.neighborhood)

            if (self.receive_and_feed_counter < len(self.peer_list) and (self.receive_and_feed_previous)):
                peer = self.peer_list[self.receive_and_feed_counter]

                self.send_chunk(peer)
                self.debt[peer] += 1

                if (self.debt[peer] > self.MAX_CHUNK_DEBT):
                    print(self.id,":",peer, "removed by unsupportive (" + str(self.debt[peer]) + " lossess)")
                    del self.debt[peer]
                    self.peer_list.remove(peer)
                    print(self.id, ":", "peer_list =", self.peer_list)
                    self.neighborhood.remove(peer)
                    print(self.id, ":", "neighborhood =", self.neighborhood)
                    # --- simulator ----------------------------------------- #
                    sim.FEEDBACK["DRAW"].put(("O","Edge","OUT",self.id,peer)) #
                    # ------------------------------------------------------- #

                #if __debug__:
                #    print(self.id, "-", str(self.receive_and_feed_previous[0]), "->", peer)

                self.receive_and_feed_counter += 1

            return chunk_number

        else:
            # A control chunk has been received
            if __debug__:
                print(self.id, ": control message received:", message)

            if message[1] == "H":

                print(self.id, ": received", message, "from", sender)
                
                # Compute RTT of hello received from peer "sender"
                self.RTTs.append((sender, time.time()-message[2]))
                print(self.id, ": RTTs =", self.RTTs)
                
                if sender not in self.peer_list:
                    self.sendto((-1, 'H', time.time()), sender)
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print(self.id, ":", sender, "added by [hello]")
                    # --- simulator ---------------------------------------------- #
                    sim.FEEDBACK["DRAW"].put(("O", "Node", "IN", sender))          #
                    sim.FEEDBACK["DRAW"].put(("O", "Edge", "IN", self.id, sender)) #
                    # ------------------------------------------------------------ #
            else:
                if sender in self.peer_list:
                    print(self.id, ": received goodbye from", sender)
                    try:
                        self.peer_list.remove(sender)
                        print(self.id, ":", sender, "removed from peer_list")
                    except:
                        print(self.id, ": failed to remove peer", sender, "from peer_list", self.peer_list)
                    print(self.id, ":", "peer_list =", self.peer_list)
                        
                    del self.debt[sender]
                    
                if sender in self.neighborhood:
                    if (self.receive_and_feed_counter > 0):
                        self.modified_list = True
                        self.receive_and_feed_counter -= 1
                    try:
                        self.neighborhood.remove(sender)
                    except:
                        print(self.id, ": failed to remove peer", sender, "from neighborhood", self.neighborhood)
                    finally:
                        print(self.id, ":", "neighborhood =", self.neighborhood)

#                    self.send_hellos(number_of_new_neighbors = 1)

                else:
                    if (sender == self.splitter):
                        print(self.id, ": received goodbye from splitter")
                        self.waiting_for_goodbye = False
            return -1

    def process_next_message(self):
        content = self.recvfrom()
        message = content[0]
        sender = content[1]
        return self.process_message(message, sender)

    def polite_farewell(self):
        print(self.id, ": (see you later)")
        while (self.receive_and_feed_counter < len(self.peer_list)):
            self.sendto(self.receive_and_feed_previous, self.peer_list[self.receive_and_feed_counter])
            self.recvfrom()
            self.receive_and_feed_counter += 1

        for peer in self.peer_list:
            self.say_goodbye(peer)

        self.ready_to_leave_the_team = True
        print(self.id, ": ready to leave the team")

    def buffer_data(self):
        self.receive_and_feed_counter = 0
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
