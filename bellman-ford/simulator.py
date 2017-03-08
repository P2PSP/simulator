import threading
import queue

queues = [queue.Queue(10)] * 10

class Node(threading.Thread):

    distances = [1000]*10       # Distance to each node
    
    def __init__(self, node):
        super(Node,self).__init__()
        self.node = node
        Node.distances[self.node] = 0

#    def define_distance_to_node(self, node, distance):
#        distances[node] = distance

    # Runs Bellman-Ford algorithm for routing between nodes
    def run(self):
        while True:

            # Compute distances
            received_distances, neighbour_node = Node.q.get()
            for i in enum(received_distances):
                if received_distances[i].distance + distances[neighbour_node] < distances[i]:
                    gateway[i] = neighbour_node
                    distances[i] = received_distances[i].distance + distances[neighbour_node]

            # Communicate distances
            for i in len(distances):
                queue[i].put(Node.distances)
                    
            for i in distances:
                print("({},{}) ",format(i, distances[i]))
