import threading
import queue
import sys
import io

queues = []

class Node(threading.Thread):

    def __init__(self, node):
        super(Node,self).__init__()
        self.node = node
        self.distances = [1000]*2 # Distance to each node
        self.gateways = [None]*2
        queues.append(queue.Queue(10))
        self.distances[self.node] = 0
        print('hola'); sys.stdout.flush()

    # Runs Bellman-Ford algorithm for routing between nodes
    def run(self):
        while True:

            found_new_route = False
            # Compute distances
            received_distances, neighbour_node = queues[self.node].get()
            print(received_distances, neighbour_node)
            for i,distance in enumerate(received_distances):
                if distance + self.distances[neighbour_node] < self.distances[i]:
                    gateways[i] = neighbour_node
                    self.distances[i] = distance + self.distances[neighbour_node]
                    found_new_route = True

            # Communicate distances
            if found_new_route:
                for i,distance in enumerate(self.distances):
                    queues[i].put((distance, i))
                    
            for i,distance in enumerate(self.distances):
                print("({},{}) ".format(i, distance))

            sys.stdout.flush()
