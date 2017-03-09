import simulator

n0 = simulator.Node(0)
n1 = simulator.Node(1)
n2 = simulator.Node(2)
n3 = simulator.Node(3)
n4 = simulator.Node(4)
n5 = simulator.Node(5)

n0.set_distance(1,3)
n0.set_distance(2,2)
n0.set_distance(3,5)

n1.set_distance(0,3)
n1.set_distance(3,1)
n1.set_distance(4,4)

n2.set_distance(0,2)
n2.set_distance(3,2)
n2.set_distance(5,1)

n3.set_distance(0,5)
n3.set_distance(1,1)
n3.set_distance(2,2)
n3.set_distance(4,3)

n4.set_distance(1,4)
n4.set_distance(3,3)
n4.set_distance(5,2)

n5.set_distance(2,1)
n5.set_distance(4,2)

n0.start()
n1.start()
n2.start()
n3.start()
n4.start()
n5.start()

# Node 0 send its vector of distances to node 1
simulator.queues[1].put((n0.get_distances(), 0))
