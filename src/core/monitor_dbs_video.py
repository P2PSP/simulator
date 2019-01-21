"""
@package simulator
monitor_dbs_video module
"""

from .common import Common
from .monitor_dbs import Monitor_DBS
from .peer_dbs_video import Peer_DBS_video


class Monitor_DBS_video(Monitor_DBS, Peer_DBS_video):
    pass
    #def play_chunk(self, chunk_number):
    #    if self.chunks[chunk_number % self.buffer_size][Common.CHUNK_NUMBER] > -1:
    #        self.player_socket.sendall(self.chunks[chunk_number % self.buffer_size][Common.CHUNK_DATA])
    #        self.chunks[chunk_number % self.buffer_size] = (-1, b'L', None)
    #        self.played += 1
    #        #print('o', end=''); sys.stdout.flush()
    #    else:
    #        self.complain(chunk_number)
    #        self.losses += 1
    #        self.lg.critical("{}: lost chunk! {} (losses = {})".format(self.ext_id, chunk_number, self.losses))
    #        if len(self.team) > 1:
    #            self.request_chunk(chunk_number, random.choice(self.team))
    #    self.number_of_chunks_consumed += 1
