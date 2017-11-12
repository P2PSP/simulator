"""
@package simulator
monitor_dbs module
"""

from .peer_dbs import Peer_DBS

class Monitor_DBS(Peer_DBS):

    def __init__(self, id):
        super().__init__(id)

    def receive_buffer_size(self):
        Peer_DBS.receive_buffer_size()
        #self.buffer_size = self.splitter_socket.recv("H")
        #print(self.id, ": received buffer_size =", self.buffer_size, "from S")
        self.buffer_size //= 2

        if __debug__:
            self.sender_of_chunks = [""]*self.buffer_size

    def complain(self, chunk_number):
        msg = struct.pack("ii", Common.REQUEST, chunk_number)
        self.team_socket.sendto(msg, self.splitter)
        lg.info("{}: [request {}] sent to {}".format(self.id, chunk_number, self.splitter))

    def play_chunk(self, chunk_number):
        if self.chunks[chunk_number % self.buffer_size][self.CHUNK] == "C":
            self.played += 1
        else:
            self.losses += 1
            print(self.id, ": lost Chunk!", chunk_number)
            self.complain(chunk_number)
        self.number_of_chunks_consumed += 1
        return self.player_alive
