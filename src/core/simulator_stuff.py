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

    #def __init__(self, id):
    #    self.id = id
    
    def send(self, message, receiver):
        message = (message, self.id)
        Simulator_stuff.TCP_SOCKETS[receiver].put(message)
        if __debug__:
            print("{} = [{}] => {}".format(self.id, message, receiver))

    def recv(self):
        (message, sender) = Simulator_stuff.TCP_SOCKETS[self.id].get()
        if __debug__:
            print("{} <= [{}] = {}".format(self.id, message, sender))
        return (message, sender)

    def sendto(self, message, receiver):
        message = (message, self.id)
        Simulator_stuff.UDP_SOCKETS[receiver].put((message))
        if __debug__:
            print("{} - [{}] -> {}".format(self.id, message, receiver))

    def recvfrom(self):
        message = Simulator_stuff.UDP_SOCKETS[self.id].get()
        if __debug__:
            print("{} <- [{}]".format(self.id, message))
        return message


