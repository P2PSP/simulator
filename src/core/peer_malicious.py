"""
@package simulator
peer_malicious module
"""
from queue import Queue
from threading import Thread
from .common import Common
from .peer_strpeds import Peer_STRPEDS
import time

class Peer_Malicious(Peer_STRPEDS):
    
    def __init__(self,id):
        super().__init__(id)
        print("Peer STRPEDS initialized")

    def first_main_target(self):
        self.main_target = self.choose_main_target()

    def choose_main_target(self):
        
