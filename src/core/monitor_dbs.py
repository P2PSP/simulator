"""
@package simulator
monitor_dbs module
"""
from queue import Queue
from threading import Thread
from .common import Common
from .peer_dbs import Peer_DBS

class Monitor_DBS(Peer_DBS):
    
    def __init__(self):
        super().__init__()
        print("DBS initialized by monitor")

    def say_hello(self, node):
        hello = (-1,"M")
        node.socket.put((self,hello))
        print("Hello sent to", node)

    def complain(self, chunk_position):
        lost = (chunk_position,"L")
        self.splitter.socketUDP(self,lost)


