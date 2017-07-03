"""
@package simulator
peer_dbs module
"""

from queue import Queue
from threading import Thread
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import team_socket
from .simulator_stuff import serve_socket #as sim
import time

class Peer_DBS(sim):
    MAX_CHUNK_DEBT = 128
    
    def __init__(self, id):
        self.id = id
        #self.socket = sim.UDP_SOCKETS[self.id]
        self.played_chunk = 0
        self.prev_received_chunk = 0
        self.buffer_size = 64
        self.player_alive = True
        self.chunks = []

        #---Only for simulation purposes----
        self.losses = 0
        self.played = 0
        self.number_of_chunks_consumed = 0
        #----------------------------------

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
        print(self.id, ": max_chunk_debt = ", self.MAX_CHUNK_DEBT)
        print(self.id, ": DBS initialized")

    def set_splitter(self, splitter):
        self.splitter = {}
        self.splitter["id"] = splitter
        #self.splitter["socketTCP"] = sim.TCP_SOCKETS[splitter]
        #self.splitter["socketUDP"] = sim.UDP_SOCKETS[splitter]

    def say_hello(self, peer):
        hello = (-1,"H")
        #sim.UDP_SOCKETS[peer].put((hello, self.id))
        print(self.id, ": sending", hello, "to", peer)
        self.sendto(hello, peer)
        #print("*********** {} sent to {}".format((hello, self.id),peer))

    def say_goodbye(self, peer):
        goodbye = (-1,"G")
        #sim.UDP_SOCKETS[peer].put((goodbye, self.id))
        print(self.id, ": sending", goodbye, "to", peer)
        self.sendto(goodbye, peer)
        #print(self.id,"Goodbye sent to", peer)

    def receive_buffer_size(self):
        #self.buffer_size, from_who = self.socket.get()
        #self.buffer_size = self.socket.get()
        #self.buffer_size = sim.UDP_SOCKETS[self.id].get()
        #self.buffer_size = sim.TCP_SOCKETS[self.id].get()
        #self.buffer_size = sim.TCP_receive(self.id)
        (self.buffer_size, sender) = self.recv()

        print(self.id,": received buffer_size =", self.buffer_size, "from", sender)

        #--- Only for simulation purposes ----
        self.sender_of_chunks = [""]*self.buffer_size
        #-------------------------------------
        
    def receive_the_number_of_peers(self):
        #self.number_of_monitors = self.socket.get()
        #self.number_of_monitors = sim.TCP_receive(self.id)
        (self.number_of_monitors, sender) = self.recv()
        print(self.id,": received number_of_monitors =", self.number_of_monitors, "from", sender)
        #self.number_of_peers = self.socket.get()
        #self.number_of_peers = sim.TCP_receive(self.id)
        (self.number_of_peers, sender) = self.recv()
        print(self.id,": received number_of_peers =", self.number_of_peers, "from", sender)
        
    def receive_the_list_of_peers(self):
        #self.peer_list = self.socket.get()[:]
        #print("-------------> 1 <------------")
        #self.peer_list = sim.TCP_receive(self.id)[:]
        (self.peer_list, sender) = self.recv()[:]
        #print("------------------> 2 <----------------")
        for peer in self.peer_list:
            self.say_hello(peer)
            self.debt[peer] = 0

        print(self.id, ": received len(peer_list) =",len(self.peer_list), "from", sender)
        print(self.id, ":", self.peer_list)

    def connect_to_the_splitter(self):
        hello = (-1,"P")
        #self.splitter["socketTCP"].put((self.id, hello))
        #sim.TCP_send((hello, self.id), self.splitter['id'])
        self.connect(hello, self.splitter['id'])
        print(self.id, ": sent", hello, "to", self.splitter['id'])

    def send_ready_for_receiving_chunks(self):
        ready = (-1, "R")
        #self.splitter["socketTCP"].put((self.id, ready))
        #sim.TCP_send(ready, self.id)
        self.send(ready, self.splitter['id'])
        #self.send(ready)
        print(self.id, ": sent", ready, "to", self.splitter['id'])

    def send_chunk(self, peer):
        #sim.UDP_SOCKETS[peer].put((self.receive_and_feed_previous, self.id))
        self.sendto(self.receive_and_feed_previous, peer)
        self.sendto_counter += 1

    def is_a_control_message(self, message):
        if message[0] == -1:
            return True
        else:
            return False
    
    def process_message(self, message, sender):
        # ----- Only for simulation purposes ------
        # ----- Check if new round for peer -------
        if not self.is_a_control_message(message) and sender == self.splitter["id"]:
            if self.played > 0 and self.played >= len(self.peer_list):
                clr = self.losses/self.played
                sim.SIMULATOR_FEEDBACK["DRAW"].put(("CLR",self.id,clr))
                self.losses = 0
                self.played = 0
        # ------------------------------------------
        
        if (message[0] >= 0):
            chunk_number = message[0]
            chunk = message[1]

            self.chunks[chunk_number % self.buffer_size] = (chunk_number, chunk)
            
            #--- for simulation purposes only ----
            self.sender_of_chunks[chunk_number % self.buffer_size] = sender

            chunks = ""
            for n,c in self.chunks:
                chunks += c
                if c == "L":
                    self.sender_of_chunks[n % self.buffer_size] = ""
                    
            sim.SIMULATOR_FEEDBACK["DRAW"].put(("B",self.id,chunks,":".join(self.sender_of_chunks)))
            #--------------------------------------
            
            self.received_counter += 1
            if (sender == self.splitter["id"]):
                while((self.receive_and_feed_counter < len(self.peer_list)) and (self.receive_and_feed_counter > 0 or self.modified_list)):
                    peer = self.peer_list[self.receive_and_feed_counter]

                    self.send_chunk(peer)
                    
                    self.debt[peer] += 1
                    
                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        
                        print(self.id,":",peer, "removed by unsupportive (", str(self.debt[peer]) , "lossess)")
                        del self.debt[peer]
                        self.peer_list.remove(peer)
                        sim.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge","OUT",self.id,peer))

                    self.receive_and_feed_counter += 1

                #Modifying the first chunk to play (it increases the delay)
                #if (not self.receive_and_feed_previous):
                    #self.played_chunk = message[0]
                    #print(self.id,"First chunk to play modified", str(self.played_chunk))

                self.modified_list = False
                self.receive_and_feed_counter = 0
                self.receive_and_feed_previous = message

                #if __debug__:
                #    print(self.id, "<-", str(chunk_number), "-", sender)
                
            else:

                #if __debug__:
                #    print(self.id, "<-", str(chunk_number), "-", sender)

                if sender not in self.peer_list:
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    if __debug__:
                        print(self.id, ":", sender, "added by chunk", chunk_number)
                    #-------- For simulation purposes only -----------
                    sim.SIMULATOR_FEEDBACK["DRAW"].put(("O","Node","IN",sender))
                    sim.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge","IN",self.id,sender))
                    #-------------------------------------------------

                else:
                    self.debt[sender] -= 1

            if (self.receive_and_feed_counter < len(self.peer_list) and (self.receive_and_feed_previous)):
                peer = self.peer_list[self.receive_and_feed_counter]

                self.send_chunk(peer)
                
                self.debt[peer] += 1
                      
                if (self.debt[peer] > self.MAX_CHUNK_DEBT):
                    print(self.id,":",peer, "removed by unsupportive (" + str(self.debt[peer]) + " lossess)")
                    del self.debt[peer]
                    self.peer_list.remove(peer)
                    sim.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge","OUT",self.id,peer))

                if __debug__:
                    print(self.id, "-", str(self.receive_and_feed_previous[0]), "->", peer)
                    
                self.receive_and_feed_counter += 1

            return chunk_number

        else:
            # A control chunk has been received
            if __debug__:
                print("Control message received", message)
                
            if message[1] == "H":
                if sender not in self.peer_list:
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    if __debug__:
                        print(self.id, ":", sender, "added by [hello]")
                    sim.SIMULATOR_FEEDBACK["DRAW"].put(("O","Node","IN",sender))
                    sim.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge","IN",self.id,sender))
            else:
                if sender in self.peer_list:
                    print(self.id, ": received goodbye from", sender)
                    self.peer_list.remove(sender)
                    del self.debt[sender]
                    if (self.receive_and_feed_counter > 0):
                        self.modified_list = True
                        self.receive_and_feed_counter -= 1
                else:
                    if (sender == self.splitter["id"]):
                        print(self.id, ": received goodbye from splitter")
                        self.waiting_for_goodbye = False
            return -1

    def process_next_message(self):
        #content = self.socket.get() #it replaces receive_next_message
        #content = sim.UDP_receive(self.id)
        content = self.recvfrom()
        #print("-------------___", content)
        message = content[0]
        sender = content[1]
        return self.process_message(message, sender)
        
    def polite_farewell(self):
        print(self.id, ": goodbye! (see you later)")
        while (self.receive_and_feed_counter < len(self.peer_list)):
            #sim.UDP_SOCKETS[self.peer_list[self.receive_and_feed_counter]].put((self.receive_and_feed_previous, self.id))
            self.sendto(self.receive_and_feed_previous, self.peer_list[self.receive_and_feed_counter])
            #content = self.socket.get()
            #conent = sim.UDP_receive(self.id)
            content = self.recvfrom()
            message = content[0]
            sender = content[1]
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
            self.chunks.append((i,"L"))
        
        chunk_number = self.process_next_message()
        
        while(chunk_number < 0):
            chunk_number = self.process_next_message()

        self.played_chunk = chunk_number

        print(self.id,": position in the buffer of the first chunk to play", str(self.played_chunk))
        
        while (chunk_number < self.played_chunk or ((chunk_number - self.played_chunk) % self.buffer_size) < (self.buffer_size // 2)):
            chunk_number = self.process_next_message()
            #while (chunk_number < 0 or chunk_number < self.played_chunk):
            while (chunk_number < self.played_chunk):
                chunk_number = self.process_next_message()
                    
        self.prev_received_chunk = chunk_number

    def play_next_chunks(self, last_received_chunk):
        for i in range(last_received_chunk - self.prev_received_chunk):
            self.player_alive = self.play_chunk(self.played_chunk)
            self.chunks[self.played_chunk % self.buffer_size] = (self.played_chunk,"L")
            self.played_chunk = (self.played_chunk + 1) % Common.MAX_CHUNK_NUMBER
        if ((self.prev_received_chunk % Common.MAX_CHUNK_NUMBER) < last_received_chunk):
            self.prev_received_chunk = last_received_chunk
    
    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number%self.buffer_size][1] == "C":
            self.played +=1
        else:
            self.losses += 1
            print (self.id, ": lost Chunk!", chunk_number)
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
                self.say_goodbye(self.splitter["id"])
        self.polite_farewell()

    def am_i_a_monitor(self):
        return self.number_of_peers < self.number_of_monitors
