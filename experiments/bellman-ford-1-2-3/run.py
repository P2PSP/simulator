import simulator
import time

n0 = simulator.Node(0)
n1 = simulator.Node(1)
n2 = simulator.Node(2)

n0.set_distance(1,1)
n1.set_distance(2,1)
n1.set_distance(0,1)
n2.set_distance(1,1)

print(n0.get_distances())
print(n1.get_distances())
print(n2.get_distances())

n0.start()
n1.start()
n2.start()

# Node 1 send its vector of distances to node 0
simulator.queues[0].put((n1.get_distances(), 1))

# Node 1 send its vector of distances to node 2
simulator.queues[2].put((n1.get_distances(), 1))

time.sleep(1)

print('After one second running ...')

print(n0.get_distances())
print(n1.get_distances())
print(n2.get_distances())
