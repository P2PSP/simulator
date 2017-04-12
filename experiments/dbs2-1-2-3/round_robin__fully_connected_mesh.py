# Create a full-connected team and serve the peers using round-robin scheduling

import fully_connected_mesh as simulator

n0 = simulator.Node(0)
n0.start()

simulator.queues[0].put((0, -1)) # Peer, chunk, splitter
simulator.queues[0].put((1, -1))

n1 = simulator.Node(1)
n1.start()

simulator.queues[0].put((2, -1))
simulator.queues[1].put((3, -1))

n2 = simulator.Node(2)
n2.start()

for i in range(10):
    simulator.queues[0].put((4+i*3, -1))
    simulator.queues[1].put((5+i*3, -1))
    simulator.queues[2].put((6+i*3, -1))

