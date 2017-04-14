# Chain commnication over a partially connected mesh.simulation (original DBS) over a fully connected team.
# Peers send only the splitter's chunk to the rest of the team.

import threading
import queue
import sys
import io
import time

max_number_of_nodes = 3
buffer_size = max_number_of_nodes
queues = [None] * max_number_of_nodes

class Node():

    def __init__(self, node_number):
        super(Node,self).__init__()
        self.node = node_number
        self.neighbors = []
        self.distances = [1000] * number_of_nodes
        self.gw = [None] * number_of_nodes # GW of each peer
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
        
