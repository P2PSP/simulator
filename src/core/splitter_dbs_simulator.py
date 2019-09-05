"""
@package p2psp-simulator
splitter_dbs_simulator module
"""

# Simulator specific behavior.

import struct
import sys
import time
from threading import Thread

from core.splitter_dbs import Splitter_DBS

from .common import Common
from .simulator_stuff import Simulator_stuff
import psutil

class Splitter_DBS_simulator(Simulator_stuff, Splitter_DBS):
    def __init__(self, name):
        super().__init__(name)
        self.lg.debug("Splitter_DBS_simulator: initialized")

    def handle_a_peer_arrival(self, connection):

        serve_socket = connection[0]
        incoming_peer = connection[1]

        print("{}: accepted connection from peer {}" .format(self.id, incoming_peer))

        # self.send_the_header()
        self.send_the_chunk_size(serve_socket)
        self.send_public_endpoint(incoming_peer, serve_socket)
        self.send_buffer_size(serve_socket)
        self.send_the_number_of_peers(serve_socket)
        self.send_the_list_of_peers(serve_socket)

        # ??????????????????????????????
        #msg_length = struct.calcsize("s")
        #msg = serve_socket.recv(msg_length)
        #message = struct.unpack("s", msg)[0]

        self.insert_peer(incoming_peer)
        sys.stderr.write(' P'+str(len(self.peer_list))); sys.stderr.flush()

        if __debug__:
            # ------------------
            # ---- Only for simulation purposes. Unknown in real implementation -----
            self.lost_chunks_from[incoming_peer] = 0
            self.received_chunks_from[incoming_peer] = 0
            msg = serve_socket.recv(struct.calcsize('!H'))
            ptype = struct.unpack('!H', msg)
            ptype = ptype[0]
            if (ptype == 0):
                self.number_of_monitors += 1
                # if Simulator_stuff.FEEDBACK:
                # Simulator_stuff.FEEDBACK["DRAW"].put(("MAP",','.join(map(str,incoming_peer)),"M"))

            # S I M U L A T I O N
            if Simulator_stuff.FEEDBACK:
                Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "IN", ','.join(map(str, incoming_peer))))
            self.lg.debug("{}: number of monitors = {}".format(self.id, self.number_of_monitors))

        serve_socket.close()

    def remove_peer(self, peer):
        self.lg.debug("{}: peer {} removed".format(self.id, peer))
        try:
            self.peer_list.remove(peer)
        except ValueError:
            self.lg.warning("{}: the removed peer {} does not exist!".format(self.id, peer))
        else:
            # self.peer_number -= 1
            if __debug__:
                # S I M U L A T I O N
                if Simulator_stuff.FEEDBACK:
                    Simulator_stuff.FEEDBACK["DRAW"].put(("O", "Node", "OUT", ','.join(map(str, peer))))
                if peer[0] == "M" and peer[1] != "P":
                    self.number_of_monitors -= 1

        try:
            del self.losses[peer]
        except KeyError:
            self.lg.warning("{}: the removed peer {} does not exist in losses".format(self.id, peer))
        finally:
            pass
        sys.stderr.write(' P'+str(len(self.peer_list))); sys.stderr.flush()

    def receive_chunk(self):
        # Simulator_stuff.LOCK.acquire(True,0.1)
        #time.sleep(Common.CHUNK_CADENCE)  # Simulates bit-rate control
        # C -> Chunk, L -> Loss, G -> Goodbye, B -> Broken, P -> Peer, M -> Monitor, R -> Ready
        #if __debug__:
            #sys.stderr.write(str(len(self.team))); sys.stderr.flush()
        time.sleep(psutil.cpu_percent()/1000.0)
        return b'C'

    def run(self):
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

        # while self.alive:
        while len(self.peer_list) > 0:

            chunk = self.receive_chunk()

            # ????
            #self.lg.info("peer_number = {}".format(self.peer_number))
            #print("peer_number = {}".format(self.peer_number))
            if self.peer_number == 0:
                sys.stderr.write(' R'+str(self.current_round)); sys.stderr.flush()
                total_peers += len(self.peer_list)
                self.on_round_beginning()  # Remove outgoing peers

                if __debug__:
                    # S I M U L A T I O N
                    if Simulator_stuff.FEEDBACK:
                        Simulator_stuff.FEEDBACK["STATUS"].put(("R", self.current_round))
                        Simulator_stuff.FEEDBACK["DRAW"].put(("R", self.current_round))
                        Simulator_stuff.FEEDBACK["DRAW"].put(("T", "M", self.number_of_monitors, self.current_round))
                        Simulator_stuff.FEEDBACK["DRAW"].put(
                            ("T", "P", (len(self.peer_list) - self.number_of_monitors), self.current_round))

            try:
                peer = self.peer_list[self.peer_number]
            except IndexError:
                self.lg.warning("{}: the peer with index {} does not exist. peer_list={} peer_number={}".format(
                    self.id, self.peer_number, self.peer_list, self.peer_number))
                # raise

            message = self.compose_chunk_packet(chunk, peer)
            self.destination_of_chunk[self.chunk_number % Splitter_DBS.buffer_size] = peer
            self.lg.debug("{}: showing destination_of_chunk:".format(self.id))
            counter = 0
            for i in self.destination_of_chunk:
                self.lg.debug("{} -> {}".format(counter, i))
                counter += 1

            self.send_chunk(message, peer)
            self.chunk_number = (self.chunk_number + 1) % Common.MAX_CHUNK_NUMBER
            try:
                self.peer_number = (self.peer_number + 1) % len(self.peer_list)
            except ZeroDivisionError:
                pass

#            self.compute_next_peer_number(peer)

            #            except IndexError:
            #                self.lg.error("{}: the monitor peer has died!".format(self.id))
            #                self.lg.error("{}: peer_list = {}".format(self.id, self.peer_list))
            #                self.lg.error("{}: peer_number = {}".format(self.id, self.peer_number))

            if __debug__:
                # S I M U L A T I O N
                if self.peer_number == 0:
                    self.current_round += 1
                    #self.lg.info("round = {}".format(self.current_round))
                    self.lg.info("{}: round={:03} chunk_number={:05} number_of_peers={:03}".format(
                        self.id, self.current_round, self.chunk_number, len(self.peer_list)))
                    #print("{}: len(peer_list)={}".format(self.id, len(self.peer_list)))
                    #sys.stderr.write(str(self.current_round) + "/" + str(self.max_number_of_rounds) + " " + str(self.chunk_number) + " " + str(len(self.peer_list)) + "\r")

        self.alive = False
        self.lg.debug("{}: alive = {}".format(self.id, self.alive))

        #counter = 0
        # while (len(self.peer_list) > 0) and (counter < 10):
        #    self.lg.info("{}: peer_list={}".format(self.id, self.peer_list))
        #    time.sleep(0.1)
        #    for p in self.peer_list:
        #        self.say_goodbye(p)
        #    counter += 1
        if Simulator_stuff.FEEDBACK:
            Simulator_stuff.FEEDBACK["STATUS"].put(("Bye", "Bye"))
            self.lg.debug("{}: Bye sent to simulator".format(self.id))

        print("{}: total peers {} in {} rounds, {} peers/round"
              .format(self.id, total_peers, self.current_round, (float)(total_peers)/(float)(self.current_round)))
        #print("{}: {} lost chunks of {}".format(self.id, self.total_lost_chunks, self.total_received_chunks, (float)(self.total_lost_chunks)/(float)(self.total_received_chunks)))
        print("{}: {} lost chunks of {}".format(self.id, self.total_lost_chunks, self.total_received_chunks))
