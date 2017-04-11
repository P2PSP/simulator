# Create a team and serve the peers using round-robin scheduling

import simulator
import time

n0 = simulator.Node(0)
n0.start()

simulator.queues[0].put((0, -1)) # Peer, chunk, splitter
simulator.queues[0].put((1, -1)) # Peer, chunk, splitter

n1 = simulator.Node(1)
n0.add_neighbor(1)
n1.add_neighbor(0)
n1.start()

simulator.queues[0].put((2, -1)) # Peer, chunk, splitter
simulator.queues[1].put((3, -1)) # Peer, chunk, splitter

n2 = simulator.Node(2)
n2.add_neighbor(1)
n1.add_neighbor(2)
print(n0.get_neighbors())
print(n1.get_neighbors())
print(n2.get_neighbors())
n2.start()

simulator.queues[0].put((4, -1)) # Peer, chunk, splitter
simulator.queues[1].put((5, -1)) # Peer, chunk, splitter
simulator.queues[2].put((6, -1)) # Peer, chunk, splitter

simulator.queues[0].put((7, -1)) # Peer, chunk, splitter
simulator.queues[1].put((8, -1)) # Peer, chunk, splitter
simulator.queues[2].put((9, -1)) # Peer, chunk, splitter

simulator.queues[0].put((10, -1)) # Peer, chunk, splitter
simulator.queues[1].put((11, -1)) # Peer, chunk, splitter
simulator.queues[2].put((12, -1)) # Peer, chunk, splitter

