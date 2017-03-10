import multiprocessing
#import threading
#import queue
import sys
import io

number_of_nodes = 6

queues = [None]*number_of_nodes

class Node():

    distances = [1000]*number_of_nodes # Distance to each node
    
    def __init__(self, node):
        super(Node,self).__init__()
        self.node = node # Node number
        self.gateways = []
        queues[self.node] = multiprocessing.Queue(10)
        #queues[self.node] = queue.Queue(10)
        Node.distances[self.node] = 0

    def set_distance(self, node, distance):
        Node.distances[node] = distance
        if not node in self.gateways:
            self.gateways.append(node)
        print('Node', self.node, 'distances =', Node.distances)

    def get_distances(self):
        return Node.distances

    # Runs Bellman-Ford algorithm for routing between nodes
    def run(self):
        print('Running node', self.node)
        while True:

            found_new_route = False

            # Compute distances
            print('Node', self.node, ': current distances =', Node.distances)
            received_distances, neighbour_node = queues[self.node].get()
            print('Node', self.node, ': Received', received_distances, 'from node', neighbour_node)
            for i,distance in enumerate(received_distances):
                print('distance=', distance, 'Node.distances[', neighbour_node, ']=', Node.distances[neighbour_node], 'Node.distances[',i,']=',Node.distances[i])
                if distance + Node.distances[neighbour_node] < Node.distances[i]:
                    Node.distances[i] = distance + Node.distances[neighbour_node]
                    found_new_route = True
                    print('Found new route!')
                    
            #import ipdb; ipdb.set_trace()
            
            # Communicate distances
            if found_new_route:
                print('Node', self.node, 'Transmiting vector of distances')
                for gw in self.gateways:
                    print("gw =",gw)
                    print("distances =", Node.distances)
                    queues[gw].put((Node.distances, self.node))

            for i,distance in enumerate(Node.distances):
                print("({},{})".format(i, distance), end=' ')
            print()

            sys.stdout.flush()

    def start(self):
        #threading.Thread(target=self.run).start()
        multiprocessing.Process(target=self.run).start()
        
