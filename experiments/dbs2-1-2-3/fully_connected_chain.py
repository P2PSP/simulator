# Chain simulation over a fully connected mesh.
# Peer i sends to i+1.

import threading
import queue
import sys
import io
import time

max_number_of_nodes = 3
buffer_size = 3
queues = [None] * max_number_of_nodes

class Node():

    number_of_nodes = 0
    
    def __init__(self, node_number):
        super(Node,self).__init__()
        self.node = node_number
        self.buffer = [None] * buffer_size
        queues[self.node] = queue.Queue(10)
        Node.number_of_nodes += 1
        
    # Run forwarding algorithm
    def run(self):

        print('Node {}: running'.format(self.node))

        while True:

            # Receive a chunk
            chunk, ttl, sender = queues[self.node].get()
            if __debug__:
                print('Node {}: {} from {}'.format(self.node, chunk, sender))
            #print('Node', self.node, ': received chunk', chunk, 'from', sender)

            # Store the chunk in the buffer
            self.buffer[chunk % buffer_size] = chunk
            print('Node {}: buffer=|'.format(self.node), end='')
            for i in self.buffer:
                if i!= None:
                    print('{:2d}|'.format(i), end='')
                else:
                    print('--|', end='')
            print()
            
            # Flooding pattern: send the received chunk to the next
            # peer of the chain.
            destination_node = (self.node + 1) % Node.number_of_nodes

            # Send the chunk
            if(ttl>0):
                queues[destination_node].put((chunk, ttl-1, self.node))
                
            if __debug__:
                print('Node', self.node, \
                      'destination_node =', destination_node, \
                      'chunk =', chunk)
            
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        threading.Thread(target=self.run).start()
        
