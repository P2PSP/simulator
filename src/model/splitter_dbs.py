"""
@package p2psp-simulator
splitter_dbs module
"""

class Splitter_DBS(Splitter_core):
    
    def __init__(self):
        self.peer_list = []
        self.losses = {}
        print("DBS initialized")

    def insert_peer(self, peer):
        if peer not in self.peer_list:
            self.peer_list_append(peer)
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
