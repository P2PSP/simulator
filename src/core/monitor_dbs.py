"""
@package simulator
monitor_dbs module
"""
from queue import Queue
from threading import Thread
from .common import Common
from .peer_dbs import Peer_DBS

class Monitor_DBS(Peer_DBS):
    
    def __init__(self,id):
        super().__init__(id)
        print("DBS initialized by monitor")

    def say_hello(self, node):
        hello = (-1,"H")
        node.socket.put((self,hello))
        print("Hello sent to", node)

    def connect_to_the_splitter(self):
        hello = (-1,"M")
        self.splitter.socketTCP.put((self,hello))

    def complain(self, chunk_position):
        lost = (chunk_position,"L")
        self.splitter.socketUDP(self,lost)


