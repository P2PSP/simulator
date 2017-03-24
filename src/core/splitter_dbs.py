"""
@package p2psp-simulator
splitter_dbs module
"""
from queue import Queue
from threading import Thread
from .splitter_core import Splitter_core
from .common import Common
import time

class Splitter_DBS(Splitter_core):
    MAX_NUMBER_OF_CHUNK_LOSS = 32
    BUFFER_SIZE = 1024
    
    def __init__(self):
        super().__init__()
        self.peer_list = []
        self.losses = {}
        self.tcp_socket = Common.TCP_SOCKETS[self.id]
        self.udp_socket = Common.UDP_SOCKETS[self.id]
        self.destination_of_chunk = []
        self.buffer_size = self.BUFFER_SIZE
        self.peer_number = 0
        self.max_number_of_chunk_loss = self.MAX_NUMBER_OF_CHUNK_LOSS
        self.number_of_monitors = 0
        self.outgoing_peer_list = []
        self.current_round = 0
        print("Splitter DBS initialized")

    def send_the_number_of_peers(self, peer):
        Common.UDP_SOCKETS[peer].put(self.number_of_monitors)
        Common.UDP_SOCKETS[peer].put(len(self.peer_list))

    def send_the_list_of_peers(self, peer):
        Common.UDP_SOCKETS[peer].put(self.peer_list)
        
    def insert_peer(self, peer):
        if peer not in self.peer_list:
            self.peer_list.append(peer)
        self.losses[peer] = 0
        print("peer inserted on splitter list", peer)

    def handle_a_peer_arrival(self):
        content = self.tcp_socket.get()
        incoming_peer = content[0]
        message = content[1]
        print(self.id,"acepted connection from peer", incoming_peer)
        print(self.id, "message", content)
        if (message[1] == "M"):
            self.number_of_monitors += 1
        print("NUMBER OF MONITORS", self.number_of_monitors)
                
        self.send_the_number_of_peers(incoming_peer)
        self.send_the_list_of_peers(incoming_peer)

        #receive_ready_for_receiving_chunks
        #check if we receive confirmation from the incoming_peer
        m = self.tcp_socket.get()
        while m[0] != incoming_peer:
            self.tcp_socket.put(m)
            m = self.tcp_socket.get()
            
        self.insert_peer(incoming_peer)
        Common.SIMULATOR_FEEDBACK["DRAW"].put(("O","Node",incoming_peer))
        
    def increment_unsupportivity_of_peer(self, peer):
        try:
            self.losses[peer] += 1
        except KeyError:
            print("The unsupportive peer", peer, "does not exist!")
        else:
            print(peer, "has loss", self.losses[peer], "chunks")
            if self.losses[peer] > Common.MAX_CHUNK_LOSS:
                print(peer, 'removed')
                self.remove_peer(peer)
        finally:
           pass     

    def process_lost_chunk(self, lost_chunk_number, sender):
        destination = get_losser(lost_chunk_number)
        print(sender,"complains about lost chunk",lost_chunk_number)
        self.increment_unsupportivity_of_peer(destination)

    def get_lost_chunk_number(self, message):
        return message[0]

    def get_losser(self,lost_chunk_number):
        return self.destination_of_chunk[lost_chunk_number % self.buffer_size]

    def remove_peer(self, peer):
        try:
            self.peer_list.remove(peer)
        except ValueError:
            pass
        else:
            self.peer_number -= 1

        try:
            del self.losses[peer]
        except KeyError:
            pass

    def process_goodbye(self, peer):
        print(self.id,"received goodbye from", peer)
        if peer not in self.outgoing_peer_list:
            if peer in self.peer_list:
                self.outgoing_peer_list.append(peer)
                print("marked for deletion, peer")

    def say_goodbye(self, peer):
        goodbye = (-1,"G")
        peer.put((self.id,goodbye))
        print("goodbye sent to", peer)
    
    def moderate_the_team(self):
        while self.alive:
            content = self.udp_socket.get()
            sender = content[0]
            message = content[1]
                        
            if (message[1] == "L"):
                lost_chunk_number = self.get_lost_chunk_number(message)
                self.process_lost_chunk(lost_chunk_number, sender)

            else:
                self.process_goodbye(sender)

    def reset_counters(self):
        for i in self.losses:
            self.losses[i] /= 2

    def reset_counters_thread(self):
        while self.alive:
            self.reset_counters()
            time.sleep(Common.COUNTERS_TIMING)

    def compute_next_peer_number(self, peer):
        self.peer_number = (self.peer_number + 1) % len(self.peer_list)

    def start(self):
        Thread(target=self.run).start()

    def run(self):
        Thread(target=self.handle_arrivals).start()
        Thread(target=self.moderate_the_team).start()
        Thread(target=self.reset_counters_thread).start()

        while self.alive:
            chunk = self.receive_chunk()
            try:
                peer = self.peer_list[self.peer_number]
                message = (self.chunk_number, chunk)
                
                self.send_chunk(message, peer)

                self.destination_of_chunk.insert(self.chunk_number % self.buffer_size, peer)
                self.chunk_number = (self.chunk_number + 1) % Common.MAX_CHUNK_NUMBER                
                self.compute_next_peer_number(peer)
            except IndexError:
                print("The monitor peer has died!")

            if self.peer_number == 0:
                Common.SIMULATOR_FEEDBACK["STATUS"].put(("R", self.current_round))
                Common.SIMULATOR_FEEDBACK["DRAW"].put(("T","M",self.number_of_monitors, self.current_round))
                Common.SIMULATOR_FEEDBACK["DRAW"].put(("T","P",(len(self.peer_list)-self.number_of_monitors), self.current_round))
                self.current_round += 1
                    
                for peer in self.outgoing_peer_list:
                    say_goodbye(peer)
                    remove_peer(peer)

            del self.outgoing_peer_list[:]
