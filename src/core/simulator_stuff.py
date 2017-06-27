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

    def UDP_send(message, receiver):
        Simulator_stuff.UDP_SOCKETS[receiver].put((message))

    def UDP_receive(sender):
        Simulator_stuff.UDP_SOCKETS[sender].get()
        
    def TCP_send(message, receiver):
        Simulator_stuff.TCP_SOCKETS[receiver].put(message)
        
    def TCP_receive(sender):
        return Simulator_stuff.TCP_SOCKETS[sender].get()
