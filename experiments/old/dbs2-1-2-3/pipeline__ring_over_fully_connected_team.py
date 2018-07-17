import __ring_over_fully_connected_team as simulator

n0 = simulator.Node(0)
n0.start()

simulator.queues[0].put((0, 0, -1))  # Peer, chunk, TTL, splitter
simulator.queues[0].put((1, 0, -1))

n1 = simulator.Node(1)
n1.start()

simulator.queues[0].put((2, 1, -1))
simulator.queues[0].put((3, 1, -1))

n2 = simulator.Node(2)
n2.start()

simulator.queues[0].put((4, 2, -1))
simulator.queues[0].put((5, 2, -1))

n3 = simulator.Node(3)
n3.start()

for i in range(50):
    simulator.queues[0].put((i + 6, 3, -1))
