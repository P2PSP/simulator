# Chain simulation over a fully connected mesh.
# Peer i sends to peer i+1.

import threading
import queue
import sys
import io
import time

max_number_of_nodes = 10
buffer_size = 40
queues = [None] * max_number_of_nodes

class Node():

    number_of_nodes = 0
    
    def __init__(self, node_number):
        super(Node, self).__init__()
        self.node = node_number
        self.buffer = [None] * buffer_size
        self.sender = [None] * buffer_size
        queues[self.node] = queue.Queue()
        
    # Run forwarding algorithm
    def run(self):

        Node.number_of_nodes += 1
        print('Node {}: running (number_of_nodes={})'.format(self.node, Node.number_of_nodes))

        while True:

            # Receive a chunk
            chunk, ttl, sender = queues[self.node].get()
            if __debug__:
                print('Node {}: received {} from {} (TTL={})'.format(self.node, chunk, sender, ttl))

            # Store the chunk in the buffer
            self.buffer[chunk % buffer_size] = chunk
            self.sender[chunk % buffer_size] = sender

            # Print the content of the buffer
            print('Node {}: buffer = '.format(self.node), end='')
            for i in self.buffer:
                if i != None:
                    print('{:2d},{:2d} '.format(i, self.sender[i]), end='')
                else:
                    print('  ,   ', end='')
            print()
                    
            # Print the content of the buffer
            #print('Node {}: buffer = '.format(self.node), end='')
            #for i in self.buffer:
            #    if i!= None:
            #        if self.sender[i] == -1:
            #            print('{:2d}*'.format(i), end='')
            #        else:
            #            print('{:2d}.'.format(i), end='')
            #    else:
            #        print('  |', end='')
            #print()
            
            # Flooding pattern: send the received chunk to the next
            # peer of the chain
            destination_node = (self.node + 1) % Node.number_of_nodes

            # Send the chunk
            if(ttl>0):
                queues[destination_node].put((chunk, ttl-1, self.node))
                if __debug__:
                    print('Node {}: sent {} to {} (number_of_nodes={})'.\
                          format(self.node, chunk, destination_node, Node.number_of_nodes))
            
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        threading.Thread(target=self.run).start()
        
