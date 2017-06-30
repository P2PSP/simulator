"""
@package simulator
simulator module
"""

"""Socket used by the splitter to send chunks to the peers and by
peers to send data (chunks for example) without ARQ.

"""
class team_socket:

    UDP_SOCKETS= {}

    #def __init__(self, id):
    #    self.id = id
    
    def sendto(self, message, receiver):
        message = (message, self.id)
        Simulator_stuff.UDP_SOCKETS[receiver].put((message))
        if __debug__:
            print("{} - {} -> {}".format(self.id, message, receiver))
            
    def recvfrom(self):
        message = Simulator_stuff.UDP_SOCKETS[self.id].get()
        if __debug__:
            print("{} <- {}".format(self.id, message))
        return message

""" Socket used by the splitter to serve to the incoming peer the data
without loss.  """
class serve_socket:

    TCP_SOCKETS = {}
    
    def TCP_send(message, receiver):
        Simulator_stuff.TCP_SOCKETS[receiver].put(message)
        if __debug__:
            print("TCP_send ({}) {}".format(receiver, message))
        
    def TCP_receive(me):
        m = Simulator_stuff.TCP_SOCKETS[me].get()
        if __debug__:
            print("TCP_receive ({}) {}".format(me, m))
        return m

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

    #def __init__(self, id):
    #    self.id = id
    
    def sendto(self, message, receiver):
        message = (message, self.id)
        Simulator_stuff.UDP_SOCKETS[receiver].put((message))
        if __debug__:
            print("{} -{}-> {}".format(self.id, message, receiver))
            
    def UDP_receive(id):
        message = Simulator_stuff.UDP_SOCKETS[id].get()
        if __debug__:
            print("{} <-{}".format(id, message))
        return message
        
    def TCP_send(message, receiver):
        Simulator_stuff.TCP_SOCKETS[receiver].put(message)
        if __debug__:
            print("TCP_send ({}) {}".format(receiver, message))
        
    def TCP_receive(me):
        m = Simulator_stuff.TCP_SOCKETS[me].get()
        if __debug__:
            print("TCP_receive ({}) {}".format(me, m))
        return m
