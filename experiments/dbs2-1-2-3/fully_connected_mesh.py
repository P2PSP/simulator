# Full-mesh simulation (original DBS) over a fully connected team.
# Peers send only the splitter's chunk to the rest of the team.

import threading
import queue
import sys
import io
import time
#import colorama

max_number_of_nodes = 3
buffer_size = 40
queues = [None] * max_number_of_nodes

class Node():

    number_of_nodes = 0
    
    def __init__(self, node_number):
        super(Node,self).__init__()
        self.node = node_number
        self.buffer = [None] * buffer_size
        self.sender = [None] * buffer_size
        queues[self.node] = queue.Queue()
        self.chunks_to_relay = []
        #colorama.init()
        
    # Run forwarding algorithm
    def run(self):

        Node.number_of_nodes += 1
        print('Node {}: running (number_of_nodes={})'.format(self.node, Node.number_of_nodes))

        destination_node = 0
        
        while True:
            
            # Receive a chunk
            chunk, sender = queues[self.node].get()

            if __debug__:
                print('Node {}: received {} from {}'.format(self.node, chunk, sender))

            # Store the chunk in the buffer
            self.buffer[chunk % buffer_size] = chunk
            self.sender[chunk % buffer_size] = sender

            # Print the content of the buffer
            print('Node {}: buffer = '.format(self.node), end='')
            for i in self.buffer:
                if i != None:
                    #print(colorama.Fore.RED + '{:2d}*'.format(i), end=colorama.Style.RESET_ALL + '')
                    print('{:2d},{:2d} '.format(i, self.sender[i]), end='')
                else:
                    print('  ,   ', end='')
            print()
            
            # Flooding pattern: send the chunk received from the
            # splitter to the rest of peers of the team

            # Each chunk should follow its own run along the list of peers.
            
            if sender == -1:

                # A new chunk has arrived from the splitter.
                self.chunks_to_relay.append((chunk, self.node)) # (chunk, first peer to send it)

            #c = 0
            for c, i in enumerate(self.chunks_to_relay):

                relayed_chunk, destination_node = i
                if __debug__:
                    print('Node {}: i={} chunks_to_relay={}'.format(self.node, i, self.chunks_to_relay))
                    
                destination_node = (destination_node + 1) % Node.number_of_nodes
                #while destination_node == self.node:
                #    destination_node = (destination_node + 1) % Node.number_of_nodes

                if destination_node == self.node:
                #if c>= (Node.number_of_nodes - 1):    
                #if destination_node == 0:
                    if __debug__:
                        print('Node {}: deleted {}'.format(self.node, self.chunks_to_relay[c]))
                    del(self.chunks_to_relay[c])
                    continue

                queues[destination_node].put((relayed_chunk, self.node))
                if __debug__:
                    print('Node {}: sent {} to {} (number_of_nodes={})'.\
                          format(self.node, relayed_chunk, destination_node, Node.number_of_nodes))
                
                self.chunks_to_relay[c] = (relayed_chunk, destination_node)

                #c += 1                    
            
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self):
        threading.Thread(target=self.run).start()

