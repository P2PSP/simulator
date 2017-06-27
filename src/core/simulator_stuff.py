"""
@package simulator
simulator module
"""
class Simulator_stuff:

    # UDP sockets for transmitting chunks from the splitter to the
    # peers. We should have so many UDP_SOCKETS as number of peers.
    UDP_SOCKETS= {}

    # TCP sockets for serving incomming peers.
    TCP_SOCKETS = {}

    # Shared lists between malicious peers.
    SHARED_LIST = {}

    # Communication channel with the simulator.
    SIMULATOR_FEEDBACK = {}

    def sendto(message, origin, destination):
        Simulator_stuff.UDP_SOCKETS[destination].put((origin, message))


    def send(message, destination):
        Simulator_stuff.TCP_SOCKETS[destination].put(message)
        
    def receive(from_who):
        return Simulator_stuff.TCP_SOCKETS[from_who].get()
