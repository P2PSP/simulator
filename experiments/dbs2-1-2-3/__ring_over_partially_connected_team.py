# Chain commnication over a partially connected mesh.  All peers
# communicate with the splitter. Peers test all the feasible
# connections with the rest of the team to determine its neighbors
# (this is not simulated here). The splitter sends a creation chain
# message to one of the peers, which selects one of its neighbors and
# sends this packet appending to it its id (ip and port in the real
# workd). The peer which receives this packet does the same and relays
# it to a different neighbors, which test if the packet has been
# retransmitted by the rest of the team (except itself). If this is
# true, the packet is sent to the origin peer and the process of the
# creation of the chain ends. If false, the packet it sent to a
# different peer. For a peer i, the chain is defined for the neighbor
# peer it selected.

import threading
import queue
import sys
import io
import time

max_number_of_nodes = 10
buffer_size = 50
queues = [None] * max_number_of_nodes

class Node():

    number_of_nodes = 0
    
    def __init__(self, node_number):
        super(Node,self).__init__()
        self.node = node_number
        self.neighbors = []
        self.distances = [1000] * max_number_of_nodes
        #self.gw = [None] * number_of_nodes # GW of each peer
        self.chunks_to_send = {} # To each neighbor
        self.buffer = [None] * buffer_size
        queues[self.node] = queue.Queue(10)
        self.distances[self.node] = 0

    def add_neighbor(self, node):
        self.neighbors.append(node)
        self.distances[node] = 1
        self.gw[node] = -1
        
    def get_neighbors(self):
        return self.neighbors

    def get_distances(self):
        return self.distances
    
    # Run forwarding algorithm
    def run(self):

        print('Node', self.node, ': running')

        neighbors_counter = 0
        found_new_route = False
        
        while True:
            # Receive a chunk
            chunk, received_distances, sender = queues[self.node].get()
            print('Node', self.node, ': received chunk', chunk, 'from', sender)

            # Compute shorter distances
            for i, distance in enumerate(received_distances):
                if distance + self.distances[sender] < self.distances[i]:
                    self.distances[i] = distance + self.distances[sender]
                    self.gw[i] = sender
                    found_new_route = True
            
            # Store the chunk in the buffer
            self.buffer[chunk % buffer_size] = chunk

            # Determine the flooding pattern for the received chunk
            # (exclude the sender of the chunk and those neighbors
            # which are closer than me from the destination).

            for node in self.neighbors:
                if node != sender:
                    self.chunks_to_send[node] = chunk

            for node in self.chunks_to_send
                    
            if len(self.neighbors) > 0:
                # Determine a destination
                destination_node = self.neighbors[neighbors_counter % len(self.neighbors)]
                while destination_node == sender:
                    neighbors_counter = ( neighbors_counter + 1 ) % len(self.neighbors)
                    destination_node = self.neighbors[neighbors_counter % len(self.neighbors)]
                    if destination_node == sender:
                        break
                    print(self.node, end='')

                if destination_node != sender:
                    # Send the chunk
                    queues[destination_node].put((chunk, self.node))
                    print('Node', self.node, ': sent chunk', chunk, 'towards', destination_node)
                
            if __debug__:
                print('Node', self.node, 'neighbors_counter =', neighbors_counter, \
                      'neighbors =', self.neighbors, \
                      'destination =', destination_node, \
                      'chunk =', chunk)
            
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        threading.Thread(target=self.run).start()
        
