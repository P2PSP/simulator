"""
@package simulator
peer_dbs2_simulator module
"""

import time
import struct
from .messages import Messages
from .peer_dbs2 import Peer_DBS2
from .peer_dbs_simulator import Peer_DBS_simulator
from .ip_tools import IP_tools
from .chunk_structure import ChunkStructure
import core.stderr as stderr
import time
import struct
from .messages import Messages


class Peer_DBS2_simulator(Peer_DBS2, Peer_DBS_simulator):

    def __init__(self, id, name = "Peer_DBS2_simulator"):
        Peer_DBS2.__init__(self)
        Peer_DBS_simulator.__init__(self, id, name)
        self.lg.debug(f"{name}: DBS2 simulator initialized")

    # Respect to DBS, request and prune messages must be unpacked.
    def unpack_message(self, packet, sender):
        msg_format = "!i" + (len(packet)-4)*'s'
        chunk_number, *i_dont_know = struct.unpack(msg_format, packet)
        if chunk_number >= 0:
            self.received_chunks += 1
            chunk = list(struct.unpack(self.packet_format, packet))
            chunk[ChunkStructure.ORIGIN_ADDR] = IP_tools.int2ip(chunk[ChunkStructure.ORIGIN_ADDR])
            chunk[ChunkStructure.HOPS] += 1
            transmission_time = time.time() - chunk[ChunkStructure.TIME]
            stderr.write(f" <-{transmission_time}->")
            self.lg.debug(f"{self.ext_id}: transmission time={transmission_time}")
            #chunk[ChunkStructure.TIME] = transmission_time
            #stderr.write(f" <-{chunk[ChunkStructure.TIME]}->")
            #stderr.write(f" {transmission_time:.2}")
            self.lg.debug(f"{self.ext_id}: received chunk {chunk} from {sender}")
            self.process_chunk(chunk, sender)
            self.send_chunks_to_the_next_neighbor()
        else:
            if chunk_number == Messages.HELLO:
                self.process_hello(sender)
            elif chunk_number == Messages.GOODBYE:
                self.process_goodbye(sender)
            elif chunk_number == Messages.REQUEST:
                _, requested_chunk = struct.unpack('!ii', packet)
                self.process_request(requested_chunk, sender)
            elif chunk_number == Messages.PRUNE:
                _, origin_ip, origin_port = struct.unpack('!iIi', packet)
                #origin = struct.unpack('!iIi', packet)
                #self.process_prune((IP_tools.int2ip(origin[1]), origin[2]), sender)
                self.process_prune((IP_tools.int2ip(origin_ip), origin_port), sender)
            else:
                stderr.write(f"{self.ext_id}: unexpected control chunk with code={chunk_number}")
        return (chunk_number, sender)
