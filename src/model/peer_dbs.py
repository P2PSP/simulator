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
        print("max_chunk_debt", self.MAX_CHUNK_DEBT)
        print("DBS initialized")

    def say_hello(self, node):
        node.put((-1,"H"))
        print("Hello sent to", node)

    def say_goodbye(self, node):
        node.put((-1,"G"))
        print("Goodbye sent to", node)
        
