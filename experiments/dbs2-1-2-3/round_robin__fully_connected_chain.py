# Create a full-connected team and serve the peers using round-robin scheduling

import fully_connected_chain as simulator

n0 = simulator.Node(0)
n0.start()

simulator.queues[0].put((0, 0, -1)) # Peer, chunk, TTL, splitter
simulator.queues[0].put((1, 0, -1))

n1 = simulator.Node(1)
n1.start()

simulator.queues[0].put((2, 1, -1))
simulator.queues[1].put((3, 1, -1))

n2 = simulator.Node(2)
n2.start()

for i in range(10):
    simulator.queues[0].put((4+i*3, 2, -1))
    simulator.queues[1].put((5+i*3, 2, -1))
    simulator.queues[2].put((6+i*3, 2, -1))

#simulator.queues[0].put((7, 2, -1))
#simulator.queues[1].put((8, 2, -1))
#simulator.queues[2].put((9, 2, -1))

#simulator.queues[0].put((10, 2, -1))
#simulator.queues[1].put((11, 2, -1))
#simulator.queues[2].put((12, 2, -1))

