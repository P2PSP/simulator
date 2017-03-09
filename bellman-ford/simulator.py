import threading
import queue
import sys
import io

number_of_nodes = 6

queues = [None]*number_of_nodes

class Node(threading.Thread):

    def __init__(self, node):
        super(Node,self).__init__()
        self.node = node
        self.distances = [1000]*number_of_nodes # Distance to each node
        self.gateways = [None]*number_of_nodes
        queues[self.node] = queue.Queue(10)
        self.distances[self.node] = 0

    # Runs Bellman-Ford algorithm for routing between nodes
    def run(self):
        while True:

            found_new_route = False

            # Compute distances
            received_distances, neighbour_node = queues[self.node].get()
            print('Node', self.node, ': Received', received_distances, 'from node', neighbour_node)
            for i,distance in enumerate(received_distances):
                print('distance=', distance, 'self.distances[', neighbour_node, ']=', self.distances[neighbour_node], 'self.distances[',i,']=',self.distances[i])
                if distance + self.distances[neighbour_node] < self.distances[i]:
                    self.gateways[i] = neighbour_node
                    self.distances[i] = distance + self.distances[neighbour_node]
                    found_new_route = True

            print('Found new route', found_new_route)
                    
            # Communicate distances
            if found_new_route:
                print(selt.node, 'Transmiting vector of distances')
                for i,distance in enumerate(self.distances):
                    queues[i].put((distance, i))
                    
            for i,distance in enumerate(self.distances):
                print("({},{})".format(i, distance), end=' ')
            print()

            sys.stdout.flush()

