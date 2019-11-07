"""
@package simulator
peer_dbs3_simulator module
"""

import time
import struct
from .messages import Messages
from .peer_dbs2_simulator import Peer_DBS2_simulator
from .peer_dbs3 import Peer_DBS3
from .ip_tools import IP_tools
from .chunk_structure import ChunkStructure
import core.stderr as stderr

class Peer_DBS3_simulator(Peer_DBS2_simulator, Peer_DBS3):

    def __init__(self, id, name = "Peer_DBS3_simulator"):
        Peer_DBS3.__init__(self)
        Peer_DBS2_simulator.__init__(self, id)
        self.lg.debug(f"{name}: DBS3 simulator initialized")

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
            self.accumulated_latency_in_the_round += transmission_time
            #stderr.write(f" <-{transmission_time}->")
            self.lg.debug(f"{self.ext_id}: transmission time={transmission_time}")
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
            elif chunk_number == Messages.REQUEST_ORIGIN:
                _, origin_ip, origin_port = struct.unpack('!iIi', packet)
                self.process_request_origin((IP_tools.int2ip(origin_ip), origin_port), sender)
            else:
                stderr.write("{self.ext_id}: unexpected control chunk with code={chunk_number}")
        return (chunk_number, sender)
