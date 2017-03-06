"""
@package p2psp-simulator
splitter_core module
"""

class Splitter_core():
    
    def __init__(self):
        self.alive = True
        print("DBS initialized")
        
    def send_chunk(self, message, destination):
       destination.put(message)
