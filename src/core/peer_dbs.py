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

    def receive_the_list_of_peers(self):
        self.peer_list = self.socket.get()
        for peer in peer_list:
            self.debt[peer] = 0

        print("list of peers received")

    def connect_to_the_splitter(self):
        
