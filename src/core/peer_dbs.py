"""
@package p2psp-simulator
peer_dbs module
"""
from queue import Queue
from common import Common

class Peer_DBS(Peer_core):
    MAX_CHUNK_DEBT = 128
    
    def __init__(self):
        self.ready_to_leave_the_team = False
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
        self.ready_to_leave_the_team = False
        print("max_chunk_debt", self.MAX_CHUNK_DEBT)
        print("DBS initialized")

    def say_hello(self, node):
        hello = (-1,"H")
        node.put((self,hello))
        print("Hello sent to", node)

    def say_goodbye(self, node):
        goodbye = (-1,"G")
        node.put((self,goodbye))
        print("Goodbye sent to", node)

    def receive_the_number_of_peers(self):
        self.number_of_monitors = self.socket.get()
        print("number of monitors received")
        self.number_of_peers = self.socket.get()
        print("number of peers received")
        
    def receive_the_list_of_peers(self):
        self.peer_list = self.socket.get()
        for peer in peer_list:
            self.debt[peer] = 0

        print("list of peers received")

    def connect_to_the_splitter(self):
        Peer_core.connect_to_the_splitter(self)

    def process_message(self, message, sender):
        if (message[0] > 0):
            chunk_number = message[0]
            chunk = message[1]
            print("Chunk",chunk_number,"received from",sender,"inserted in", (chunk_number % self.buffer_size))
            self.received_counter += 1
            if (sender == self.splitter):
                while((self.receive_and_feed_counter < len(self.peer_list)) and (self.receive_and_feed_counter > 0 or self.modified_list)):
                    peer = self.peer_list[self.receive_and_feed_counter]
                    peer.socket.put(self.receive_and_feed_previous)
                    self.sendto_counter += 1

                    print(self,",",self.receive_and_feed_previous[0],"->", peer)

                    self.debt[peer] += 1
                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        print(peer, "removed by unsupportive (", str(self.debt[peer]) , "lossess)")
                        del self.debt[peer]
                        self.peer_list.remove(peer)

                    self.receive_and_feed_counter += 1

                if (self.receive_and_feed_previous == ""):
                    self.played_chunk = message[0]
                    print("First chunk to play modified", str(self.played_chunk))

                self.modified_list = False
                print("sent",str(self.receive_and_feed_counter,"of",str(self.peer_list.size()))
                print("Last chunk saved in receive and feed", str(message[0]))
                self.receive_and_feed_counter = 0
                self.receive_and_feed_previous = message
                
            else:
                
                print(self, "<-", str(self.chunk_number), "-", sender)

                if sender not in self.peer_list:
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print(sender, "added by chunk", chunk_number)
                else:
                    self.debt[sender] -= 1

            if (self.receive_and_feed_counter < len(self.peer_list) and (self.receive_and_feed_previous != "")):
                peer = self.peer_list[self.receive_and_feed_counter]
                peer.socket.put(self.receive_and_feed_previous)
                self.sendto_counter += 1
                self.debt[peer] += 1
                      
                if (self.debt[peer] > self.MAX_CHUNK_DEBT):
                      print(peer, "removed by unsupportive (" + str(self.debt[peer]) + " lossess)")
                      del self.debt[peer]
                      self.peer_list.remove(peer)

                print(self, "-", self.receive_and_feed_previous[0]), "->", peer)
                self.receive_and_feed_counter += 1
           
            return chunk_number

        else:
            # A control chunk has been received
            print("Control message received")
            if message[1] == "H":
                if sender not in self.peer_list:
                    self.peer_list.append(sender)
                    self.debt[sender] = 0
                    print(sender, "added by [hello]")
            else:
                if sender in self.peer_list:
                    print(self, "received goodbye from", sender)
                    self.peer_list.remove(sender)
                    del self.debt[sender]
                    if (self.receive_and_feed_counter > 0):
                        self.modified_list = True
                        self.receive_and_feed_counter -= 1
                else:
                    if (sender == self.splitter):
                        print("goodbye received from splitter")
                        self.waiting_for_goodbye = False
            return -1

    def pollite_farewell(self):
        print("Goodbye!")
        while (self.receive_and_feed_counter < self.peer_list.size()):
            self.peer_list[self.receive_and_feed_counter].socket.put(self.receive_and_feed_previous)
            content = self.socket.get()
            sender = content[0]
            message = content[1]
            self.receive_and_feed_counter += 1

        for (peer in self.peer_list):
            say_goodbye(peer)

        self.ready_to_leave_the_team = True
        print("Ready to leave the team")

    def buffer_data(self):
        self.receive_and_feed_counter = 0
        self.receive_and_feed_previous = ()
        self.sendto_counter = 0
        self.debt_memory = 1 << self.MAX_CHUNK_DEBT
        self.waiting_for_goodbye = True
        Peer_core.buffer_data(self)

    def run(self):
        while (self.player_alive or self.waiting_for_goodbye):
            self.keep_the_buffer_full()
            if (!self.player_alive):
                self.say_goodbye(self.splitter)
        self.polite_farewell()

    def am_i_a_monitor(self):
        return self.number_of_peers < self.number_of_monitors
