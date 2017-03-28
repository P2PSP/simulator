"""
@package simulator
peer_strpeds module
"""
from queue import Queue
from threading import Thread
from .common import Common
from .peer_dbs import Peer_DBS
import time

class Peer_STRPEDS(Peer_DBS):
    MAX_CHUNK_DEBT = 128
    
    def __init__(self,id):
        super().__init__(id)
        self.bad_peers = []
        print("Peer STRPEDS initialized")

    def receive_dsa_key(self):
        #Not needed for simulation
        return NotImplementedError

    def process_bad_message(self, message, sender):
        self.bad_peers.append(sender)
        self.peer_list.remove(sender)

    def is_a_control_message(self, message):
        if message[0] == -1:
            return True
        else:
            return False

    def check_message(self, message, sender):
        if sender in self.bad_peers:
            if __debug__:
                print("Sender is in bad peer list:",sender) 
            return false

        if not is_a_control_message(message):
            if message[1] == "C":
                return True
            else: #(L)ost or (B)roken
                return False
        else:
            if __debug__:
                print("Sender sent a control message", message)
            pass

    def handle_bad_peers_request(self):
        self.splitter["socketUDP"].put(self.id,self.bad_peers)
        if __debug__:
            print("Bad peers sent to the Splitter")


    def process_message(self, message, sender):

        if sender in self.bad_peers:
            if __debug__:
                print("Sender is  in the bad peer list", sender)
            return -1

        # ------------

        # WORKING HERE

        # ------------

        
        if (message[0] >= 0):
            chunk_number = message[0]
            chunk = message[1]

            self.chunks[chunk_number % self.buffer_size] = (chunk_number, chunk)
            #Common.SIMULATOR_FEEDBACK["BUFFER"].put(("IN",self.id,(chunk_number % self.buffer_size)))

            chunks = ""
            for n,c in self.chunks:
                chunks += c
            Common.SIMULATOR_FEEDBACK["DRAW"].put(("B",self.id,chunks))
            
            #print("Chunk",chunk_number,"received from",sender,"inserted in", (chunk_number % self.buffer_size))
            self.received_counter += 1
            if (sender == self.splitter["id"]):
                while((self.receive_and_feed_counter < len(self.peer_list)) and (self.receive_and_feed_counter > 0 or self.modified_list)):
                    peer = self.peer_list[self.receive_and_feed_counter]

                    Common.UDP_SOCKETS[peer].put((self.id,self.receive_and_feed_previous))

                    self.sendto_counter += 1
                    if __debug__:
                        print(self.id,",",self.receive_and_feed_previous[0],"->", peer)
                    
                    self.debt[peer] += 1
                    
                    if self.debt[peer] > self.MAX_CHUNK_DEBT:
                        
                        print(peer, "removed by unsupportive (", str(self.debt[peer]) , "lossess)")
                        del self.debt[peer]
                        self.peer_list.remove(peer)

                    self.receive_and_feed_counter += 1

                if (not self.receive_and_feed_previous):
                    self.played_chunk = message[0]
                    print("First chunk to play modified", str(self.played_chunk))

                self.modified_list = False
                #print("sent",str(self.receive_and_feed_counter),"of",len(self.peer_list))
                #print("Last chunk saved in receive and feed", str(message[0]))
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
                    Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Node",sender))
                    Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge",self.id,sender))

                else:
                    self.debt[sender] -= 1

            if (self.receive_and_feed_counter < len(self.peer_list) and (self.receive_and_feed_previous)):
                peer = self.peer_list[self.receive_and_feed_counter]

                Common.UDP_SOCKETS[peer].put((self.id, self.receive_and_feed_previous))

                self.sendto_counter += 1
                self.debt[peer] += 1
                      
                if (self.debt[peer] > self.MAX_CHUNK_DEBT):
                    print(peer, "removed by unsupportive (" + str(self.debt[peer]) + " lossess)")
                    del self.debt[peer]
                    self.peer_list.remove(peer)

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
                    Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Node",sender))
                    Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Edge",self.id,sender))
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
