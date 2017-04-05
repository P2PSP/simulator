import simulator
import time

n0 = simulator.Node(0)
n1 = simulator.Node(1)
n2 = simulator.Node(2)

# Set absolute distances statically
n0.set_distance(1,1)
n0.set_distance(2,2)
n1.set_distance(2,1)
n1.set_distance(0,1)
n2.set_distance(0,2)
n2.set_distance(1,1)

print(n0.get_distances())
print(n1.get_distances())
print(n2.get_distances())

n0.start()
n1.start()
n2.start()

simulator.queues[0].put((0, -1)) # Peer, chunk, splitter


