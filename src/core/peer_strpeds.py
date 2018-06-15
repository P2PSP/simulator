"""
@package simulator
peer_strpeds module
"""
from .common import Common
from .simulator_stuff import Simulator_stuff as sim
from .simulator_stuff import Simulator_socket as socket
from .peer_dbs import Peer_DBS
import struct



class Peer_STRPEDS(Peer_DBS):
    def __init__(self, id):
        super().__init__(id)
        self.bad_peers = []
        print("Peer STRPEDS initialized")

    def receive_dsa_key(self):
        # Not needed for simulation
        return NotImplementedError

    def process_bad_message(self, message, sender):
        print(self.id, "adding", sender, "to bad list", message)
        self.bad_peers.append(sender)
        if self.id in self.forward and sender in self.forward[self.id]:
            self.forward[self.id].remove(sender)
        sim.FEEDBACK["DRAW"].put(("O", "Edge", "OUT", ','.join(map(str,self.id)), ','.join(map(str,sender))))

    def check_message(self, message, sender):
        if not self.is_a_control_message(message):
            if message[1] == b"C":
                return True
            else:  # (L)ost or (B)roken
                return False
        else:
            if __debug__:
                print(self.id, "Sender sent a control message", message)
            return True

    def handle_bad_peers_request(self):
        for b in self.bad_peers:
            bad_msg = (-1, b'S', socket.ip2int(b[0]),b[1])
            msg = struct.pack('isli',*bad_msg)
            self.team_socket.sendto(msg, self.splitter)
        if __debug__:
            print(self.id, "Bad peers sent to the Splitter", self.bad_peers)
        return (-1,-1)
        

    def process_message(self, message, sender):
        if sender in self.bad_peers:
            if __debug__:
                print(self.id, "Sender is  in the bad peer list", sender)
            return (-1,-1)

        if self.check_message(message, sender):
            if self.is_a_control_message(message) and len(message)>1 and message[1] == 'S':
                return self.handle_bad_peers_request()
            else:
                return Peer_DBS.process_message(self, message, sender)
        else:
            self.process_bad_message(message, sender)
            return self.handle_bad_peers_request()

        return (-1,-1)
