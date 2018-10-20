"""
@package p2psp-simulator
splitter_dbs_video module
"""

# Implements video transmissions.

import sys
import os
import time
import struct
from threading import Thread
from .simulator_stuff import Simulator_socket as socket
from .splitter_dbs import Splitter_DBS
from .common import Common

class Splitter_DBS_video(Splitter_DBS):

    channel = "LBBB.ogv"
    buffer_size = 128
    chunk_size = 1024
    header_chunks = 30000//chunk_size
    source_address = "localhost"
    source_port = 8000

    def __init__(self, name):
        super().__init__(name)
        
        self.source = (Splitter_DBS_video.source_address, Splitter_DBS_video.source_port)
        self.lg.debug("{}: source={}".format(name, self.source))
        self.GET_message = 'GET /' + Splitter_DBS_video.channel + ' HTTP/1.1\r\n'
        self.GET_message += '\r\n'

        self.chunk_packet_format = "!i" \
            + str(Splitter_DBS_video.chunk_size) \
            + "sIi"

        self.header = b''
        self.header_load_counter = Splitter_DBS_video.header_chunks
        
        self.lg.debug("Splitter_DBS_video: initialized")

    def request_the_video_from_the_source(self):
        self.lg.debug("{}: connecting to {}".format(self.id, self.source))
        self.source_socket = socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.source_socket.connect(self.source)
        except socket.error as e:
            self.lg.error("{}: Exception: {} from {}".format(self.id, e, self.source))
            self.source_socket.close()
            os._exit(1)
        self.lg.debug("{}: connected to {}".format(self.id, self.source))
        self.source_socket.sendall(self.GET_message.encode())
        self.lg.debug("{}: GET_message={}".format(self.id, self.GET_message))

    def send_the_chunk_size(self, peer_serve_socket):
        self.lg.debug("{}: Sending chunk_size={}".format(self.id, Splitter_DBS_video.chunk_size))
        message = struct.pack("!H", (Splitter_DBS_video.chunk_size))
        peer_serve_socket.sendall(message)

    def receive_next_chunk(self):
        chunk = self.source_socket.recv(Splitter_DBS_video.chunk_size)
        print("R", end=""); sys.stdout.flush()
        prev_size = 0
        while len(chunk) < Splitter_DBS_video.chunk_size:
            if len(chunk) == prev_size:
                # This section of code is reached when the streaming
                # server (Icecast) finishes a stream and starts with
                # the following one.
                self.lg.debug("{}: End of the stream reached!".format(self.id))
                sys.stdout.flush()
                self.source_socket.close()
                time.sleep(1)
                self.source_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.source_socket.connect(self.source)
                self.source_socket.sendall(self.GET_message.encode())
                self.header = b''
                self.header_load_counter = Splitter_DBS_video.header_chunks
                #_print_("1: header_load_counter =", self.header_load_counter)
                chunk = b""
            prev_size = len(chunk)
            chunk += self.source_socket.recv(Splitter_DBS_video.chunk_size - len(chunk))
        return chunk

    #def load_the_video_header(self):
    #    self.header = b''
    #    for i in range(self.HEADER_SIZE):
    #        self.header += self.receive_next_chunk()

    def receive_chunk(self):
        chunk = self.receive_next_chunk()
        if self.header_load_counter > 0:
            self.header += chunk
            self.header_load_counter -= 1
            self.lg.debug("{}: Loaded {} bytes of header".format(self.id, len(self.header)))
        return chunk

    #def send_header_chunks(self, serve_socket):
    #    self.lg.debug("{}: Sending header_chunks={}".format(self.id, Splitter_DBS_video.header_chunks))
    #    message = struct.pack("!H", Splitter_DBS_video.header_chunks)
    #    serve_socket.sendall(message)
    def send_header_bytes(self, serve_socket):
        self.lg.debug("{}: sending header of size {} bytes".format(self.id, len(self.header)))
        message = struct.pack("!H", len(self.header))
        serve_socket.sendall(message)
    
    def send_header(self, serve_socket):
        self.lg.debug("{}: sending header of {} bytes".format(self.id, len(self.header)))
        #peer_serve_socket = connection[0]
        serve_socket.sendall(self.header)

    #def handle_a_peer_arrival(self, connection):
    #    self.send_the_header(connection)
    #    Splitter_DBS.handle_a_peer_arrival(self, connection)

    def run(self):

        chunk_counter = 0
        self.received_chunks_from = {}
        self.lost_chunks_from = {}
        self.total_received_chunks = 0
        self.total_lost_chunks = 0
        total_peers = 0

        Thread(target=self.handle_arrivals).start()
        Thread(target=self.moderate_the_team).start()
        Thread(target=self.reset_counters_thread).start()

        while len(self.peer_list) == 0:
            print("{}: waiting for a monitor at {}"
                  .format(self.id, self.id))
            time.sleep(1)
        print()
        self.request_the_video_from_the_source()

        while len(self.peer_list) > 0:

            chunk = self.receive_chunk()
            chunk_counter += 1

            # ????
            #self.lg.info("peer_number = {}".format(self.peer_number))
            #print("peer_number = {}".format(self.peer_number))
            if self.peer_number == 0:
                total_peers += len(self.peer_list)
                self.on_round_beginning()  # Remove outgoing peers

            try:
                peer = self.peer_list[self.peer_number]
            except IndexError:
                self.lg.warning("{}: the peer with index {} does not exist. peer_list={} peer_number={}".format(self.id, self.peer_number, self.peer_list, self.peer_number))
                # raise

            message = self.compose_chunk_packet(chunk, peer)
            self.destination_of_chunk[self.chunk_number % Splitter_DBS.buffer_size] = peer
            #if __debug__:
            #    self.lg.debug("{}: showing destination_of_chunk:".format(self.id))
            #    counter = 0
            #    for i in self.destination_of_chunk:
            #        self.lg.debug("{} -> {}".format(counter, i))
            #        counter += 1
            #            try:
            self.send_chunk(message, peer)
            self.chunk_number = (self.chunk_number + 1) % Common.MAX_CHUNK_NUMBER
            try:
                self.peer_number = (self.peer_number + 1) % len(self.peer_list)
            except ZeroDivisionError:
                pass

        if __debug__:
            if self.peer_number == 0:
                self.current_round += 1

        self.alive = False
        self.lg.debug("{}: alive = {}".format(self.id, self.alive))

        if __debug__:
            print("{}: total peers {} in {} rounds, {} peers/round".format(self.id, total_peers, self.current_round, (float)(total_peers)/(float)(self.current_round)))
            print("{}: {} lost chunks of {}".format(self.id, self.total_lost_chunks, self.total_received_chunks))
