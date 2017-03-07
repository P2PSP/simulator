"""
@package p2psp-simulator
splitter_dbs module
"""
from threading import Thread

class Splitter_DBS(Splitter_core):
    MAX_NUMBER_OF_CHUNK_LOSS = 32
    NUMBER_OF_MONITORS = 1
    
    def __init__(self):
        self.peer_list = []
        self.losses = {}
        self.socket = Queue()
        self.destination_of_chunk = []
        self.buffer_size = 1024
        self.peer_number = 0
        self.max_number_of_chunk_loss = self.MAX_NUMBER_OF_CHUNK_LOSS
        self.number_of_monitors = self.NUMBER_OF_MONITORS
        self.outgoing_peer_list = []
        print("DBS initialized")

    def send_the_number_of_peers(self, peer):
        peer.socket.put(self.number_of_monitors)
        peer.socket.put(len(self.peer_list))

    def send_the_list_of_peers(self, peer):
        peer.socket.put(self.peer_list)
        
    def insert_peer(self, peer):
        if peer not in self.peer_list:
            self.peer_list.append(peer)
        self.losses[peer] = 0
        print("peer inserted", peer)

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
        print("received goodbye from", peer)
        if peer not in self.outgoing_peer_list:
            if peer in self.peer_list:
                self.outgoing_peer_list.append(peer)
                print("marked for deletion, peer")

    def say_goodbye(self, peer):
        goodbye = (-1,"G")
        peer.put((self,goodbye))
        print("goodbye sent to", peer)
    
    def moderate_the_team(self):
        while self.alive:
            content = socket.get()
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

    def run(self):
        Thread(target=self.moderate_the_team).start()
        Thread(target=self.reset_counters_thread).start()
        
         while self.alive:
            chunk = self.receive_chunk()
            try:
                peer = self.peer_list[self.peer_number]
                message = (self.chunk_number, chunk)
                
                self.send_chunk(message, peer)

                self.destination_of_chunk[self.chunk_number % self.BUFFER_SIZE] = peer
                self.chunk_number = (self.chunk_number + 1) % Common.MAX_CHUNK_NUMBER
                self.compute_next_peer_number(peer)
            except IndexError:
                print("The monitor peer has died!")

            if self.peer_number == 0:
                for peer in outgoing_peer_list:
                    say_goodbye(peer)
                    remove_peer(peer)

            del outgoint_peer_list[:]
