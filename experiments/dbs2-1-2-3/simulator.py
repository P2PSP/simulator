import threading
import queue
import sys
import io
import time

number_of_nodes = 3
buffer_size = number_of_nodes

queues = [None]*number_of_nodes

class Node():

    def __init__(self, node):
        super(Node,self).__init__()
        self.node = node # Node number
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

        neighbors_counter = 0
        while True:
            # Receive a chunk
            chunk, sender = queues[self.node].get()
            print('Node', self.node, ': received chunk', chunk, 'from', sender)
            
            # Store the chunk in the buffer
            self.buffer[chunk % buffer_size] = chunk

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
        
