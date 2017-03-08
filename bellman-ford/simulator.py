import threading
import queue

team = [] # List of nodes

class Node(threading.Thread):

    q = queue.Queue(10)
    distances = []       # Distance to each node
    
    def __init__(self, iters=10):
        super(Node,self).__init__()

    def define_distance_to_none(self, node, distance):
        distances[node] = distance

    # Runs Bellman-Ford algorithm for routing between nodes
    def run(self):
        while (received_distances, neighbour_node) = q.get():
            for i in enum(received_distances):
                if received_distances[i].distance + distances[neighbour_node] < distances[i]:
                    gateway[i] = neighbour_node
                    distance[i] = received_distances[i].distance + distances[neighbour_node]

            for i in distances:
                print("({},{}) ",format(i, distances[i]))
