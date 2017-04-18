"""
@package simulator
peer_dbs module
"""
from queue import Queue
from threading import Thread
from .common import Common
from .peer_core import Peer_core
import time

class Peer_DBS(Peer_core):
    MAX_CHUNK_DEBT = 128
    
    def __init__(self,id):
        super().__init__(id)
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
        print("max_chunk_debt", self.MAX_CHUNK_DEBT)
        print("Peer DBS initialized")

    def say_hello(self, peer):
        hello = (-1,"H")
        Common.UDP_SOCKETS[peer].put((self.id,hello))
        print("Hello sent to", peer)

    def say_goodbye(self, peer):
        goodbye = (-1,"G")
        Common.UDP_SOCKETS[peer].put((self.id,goodbye))
        print("Goodbye sent to", peer)

    def receive_buffer_size(self):
        self.buffer_size = self.socket.get()
        print(self.id,"buffer size received", self.buffer_size)

        #--- Only for simulation purposes ----
        self.sender_of_chunks = [""]*self.buffer_size
        #-------------------------------------
        
    def receive_the_number_of_peers(self):
        self.number_of_monitors = self.socket.get()
        print(self.id,"number of monitors received")
        self.number_of_peers = self.socket.get()
        print(self.id,"number of peers received")
        
    def receive_the_list_of_peers(self):
        self.peer_list = self.socket.get()[:]
        
        for peer in self.peer_list:
            self.say_hello(peer)
            self.debt[peer] = 0

        print("list of peers received. Size",len(self.peer_list))

    def connect_to_the_splitter(self):
        Peer_core.connect_to_the_splitter(self)

    def send_chunk(self, peer):
        Common.UDP_SOCKETS[peer].put((self.id,self.receive_and_feed_previous))
        self.sendto_counter += 1

    def process_message(self, message, sender):
        Peer_core.process_message(self, message, sender)
        if (message[0] >= 0):
            chunk_number = message[0]
            chunk = message[1]

            self.chunks[chunk_number % self.buffer_size] = (chunk_number, chunk)
            
            #--- for simulation purposes only ----
            self.sender_of_chunks[chunk_number % self.buffer_size] = sender

            chunks = ""
            for n,c in self.chunks:
                chunks += c
            Common.SIMULATOR_FEEDBACK["DRAW"].put(("B",self.id,chunks))
            Common.SIMULATOR_FEEDBACK["DRAW"].put(("S",self.id,",".join(self.sender_of_chunks)))
            #--------------------------------------
            
            self.received_counter += 1
            if (sender == self.splitter["id"]):
                while((self.receive_and_feed_counter < len(self.peer_list)) and (self.receive_and_feed_counter > 0 or self.modified_list)):
                    peer = self.peer_list[self.receive_and_feed_counter]

                    self.send_chunk(peer)
                    
                    if __debug__:
                        print(self.id,",",self.receive_and_feed_previous[0],"->", peer)
                    
                    self.debt[peer] += 1
                    
                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        
                        print(self.id,":",peer, "removed by unsupportive (", str(self.debt[peer]) , "lossess)")
                        del self.debt[peer]
                        self.peer_list.remove(peer)
                        Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge","OUT",self.id,peer))

                    self.receive_and_feed_counter += 1

                #Modifying the first chunk to play (it increases the delay)
                #if (not self.receive_and_feed_previous):
                    #self.played_chunk = message[0]
                    #print(self.id,"First chunk to play modified", str(self.played_chunk))

                self.modified_list = False
                self.receive_and_feed_counter = 0
                self.receive_and_feed_previous = message

                if __debug__:
                    print(self.id, "<-", str(chunk_number), "-", sender)
                
            else:

                if __debug__:
                    print(self.id, "<-", str(chunk_number), "-", sender)

                if sender not in self.peer_list:
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    if __debug__:
                        print(sender, "added by chunk", chunk_number)
                    Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Node","IN",sender))
                    Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge","IN",self.id,sender))

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
                    Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge","OUT",self.id,peer))

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
                        print(sender, "added by [hello]")
                    Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Node","IN",sender))
                    Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge","IN",self.id,sender))
            else:
                if sender in self.peer_list:
                    print(self.id, "received goodbye from", sender)
                    self.peer_list.remove(sender)
                    del self.debt[sender]
                    if (self.receive_and_feed_counter > 0):
                        self.modified_list = True
                        self.receive_and_feed_counter -= 1
                else:
                    if (sender == self.splitter["id"]):
                        print("goodbye received from splitter")
                        self.waiting_for_goodbye = False
            return -1

    def polite_farewell(self):
        print("Goodbye!")
        while (self.receive_and_feed_counter < len(self.peer_list)):
            Common.UDP_SOCKETS[self.peer_list[self.receive_and_feed_counter]].put((self.id,self.receive_and_feed_previous))
            content = self.socket.get()
            sender = content[0]
            message = content[1]
            self.receive_and_feed_counter += 1

        for peer in self.peer_list:
            self.say_goodbye(peer)

        self.ready_to_leave_the_team = True
        print("Ready to leave the team")

    def buffer_data(self):
        self.receive_and_feed_counter = 0
        self.receive_and_feed_previous = ()
        self.sendto_counter = 0
        self.debt_memory = 1 << self.MAX_CHUNK_DEBT
        self.waiting_for_goodbye = True
        Peer_core.buffer_data(self)

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
