import threading
import queue
import sys
import io

number_of_nodes = 3
buffer_size = number_of_nodes

queues = [None]*number_of_nodes

class Node():

    def __init__(self, node):
        super(Node,self).__init__()
        self.node = node # Node number
        self.gateways = []
        self.distances = [1000]*number_of_nodes # Distance to each node
        queues[self.node] = queue.Queue(10)
        self.distances[self.node] = 0

    def set_distance(self, node, distance):
        self.distances[node] = distance
        if not node in self.gateways:
            self.gateways.append(node)
        print('Node', self.node, ': distances =', self.distances)

    def get_distances(self):
        return self.distances

    # Run forwarding algorithm
    def run(self):

        print('Node', self.node, ': running')

        # Simulate the reception of the neighbors_list
        neighbors_list = []
        for node, distance in enumerate(self.distances):
            if distance == 1:
                neighbors_list.append(node)
        print('Node', self.node, ':', neighbors_list)

        # Create the buffer
        _buffer = [None] * buffer_size

        neighbors_counter = 0
        while True:
            # Receive a chunk from node neighbor
            chunk, neighbor = queues[self.node].get()
            print('Node', self.node, ': received chunk', chunk, 'from', neighbor)
            
            # Store the chunk in the buffer
            _buffer[chunk % buffer_size] = chunk

            # Send the chunk
            destination_node = neighbors_counter % len(neighbors_list)
            queues[destination_node].put((chunk, self.node))
            print('Node', self.node, 'neighbors_counter =', neighbors_counter, \
                  'neighbors_list =', neighbors_list, \
                  'destination =', destination_node, \
                  'chunk =', chunk)
            neighbors_counter = ( neighbors_counter + 1 ) % len(neighbors_list)

            sys.stdout.flush()

    def start(self):
        threading.Thread(target=self.run).start()
        
