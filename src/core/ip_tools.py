"""
@package simulator
simulator module
"""

import socket
import struct

class IP_tools():

    # This function should be moved to a different class named IP_tools
    def ip2int(addr):
        return struct.unpack("!I", socket.inet_aton(addr))[0]

    # Idem
    def int2ip(addr):
        return socket.inet_ntoa(struct.pack("!I", addr))
