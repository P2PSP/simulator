"""
@package simulator
peer_core module
"""
from queue import Queue
from .common import Common
import time

class Peer_core():
    def __init__(self, id):
        self.id = id
        self.socket = Queue()
        self.played_chunk = 0
        self.prev_received_chunk = 0
        self.buffer_size = 1024
        self.player_alive = True
        print("Peer Core initialized")

    def set_splitter(self, splitter):
        self.splitter = splitter

    def connect_to_the_splitter(self):
        hello = (-1,"P")
        self.splitter.socketTCP.put((self,hello))

    def send_ready_for_receiving_chunks(self):
        ready = (-1, "R")
        self.splitter.socketTCP.put((self,ready))

    def process_message(self, message, sender):
        raise NotImplementedError

    def process_next_message(self):
        content = self.socket.get() #replaces receive_next_message
        return self.process_message(content[1], content[0])

    def buffer_data(self):
        chunk_number = self.process_next_message()
        min_chunk_number = chunk_number

        while(chunk_number < 0):
            chunk_number = self.process_next_message()

        if (min_chunk_number < chunk_number):
            min_chunk_number = chunk_number

        self.played_chunk = min_chunk_number % self.buffer_size

        while (((chunk_number - self.played_chunk) % self.buffer_size) < self.buffer_size / 2):
            chunk_number = self.process_next_message()
            while (chunk_number < 0):
                if (chunk_number < min_chunk_number):
                    self.played_chunk = min_chunk_number
                chunk_number = self.process_next_message()
        self.prev_received_chunk = chunk_number

    def keep_the_buffer_full(self):
        last_received_chunk = self.process_next_message()
        while (last_received_chunk < 0):
            last_received_chunk = self.process_next_message()

        self.play_next_chunks(last_received_chunk)

    def play_next_chunks(self, last_received_chunk):
        for i in range(last_received_chunk - self.prev_received_chunk):
           self.player_alive = self.play_chunk(self.played_chunk)
           #LOG chunks consumed and lost chunks
           self.played_chunk = (self.played_chunk + 1) % Common.MAX_CHUNK_NUMBER
        if ((self.prev_received_chunk % Common.MAX_CHUNK_NUMBER) < last_received_chunk):
            self.prev_received_chunk = last_received_chunk
    
    def play_chunk(self, chunk_number):
        #print("chunk", chunk_number, "consumed")
        return True

    def run(self):
        while(self.player_alive):
            keep_the_buffer_full()
