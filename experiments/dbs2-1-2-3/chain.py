# Chain simulation
# Peers send to their higher peer id.

import threading
import queue
import sys
import io
import time

number_of_nodes = 3
buffer_size = number_of_nodes

queues = [None]*number_of_nodes

class Node():

    def __init__(self, node_number):
        super(Node,self).__init__()
        self.node = node_number
        self.neighbors = []
        self.buffer = [None] * buffer_size
        queues[self.node] = queue.Queue(10)

    def add_neighbor(self, node):
        self.neighbors.append(node)
        
    def get_neighbors(self):
        return self.neighbors

    # Run forwarding algorithm
    def run(self):

        print('Node', self.node, ': running')

        while True:

            # Receive a chunk
            chunk, ttl, sender = queues[self.node].get()
            print('Node {}: {} from {}'.format(self.node, chunk, sender))
            #print('Node', self.node, ': received chunk', chunk, 'from', sender)

            # Store the chunk in the buffer
            self.buffer[chunk % buffer_size] = chunk

            # Flooding pattern: send the received chunk to the next
            # peer of the chain.
            destination_node = (self.node + 1) % number_of_nodes

            # Send the chunk
            if(ttl>0):
                queues[destination_node].put((chunk, ttl-1, self.node))
                
            if __debug__:
                print('Node', self.node, \
                      'neighbors =', self.neighbors, \
                      'destination_node =', destination_node, \
                      'chunk =', chunk)
            
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        threading.Thread(target=self.run).start()
        
