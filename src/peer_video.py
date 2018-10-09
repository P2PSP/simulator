import argparse
import logging
from core.peer_dbs import Peer_DBS
from core.peer_ims import Peer_IMS
from peer import Peer

class Peer_video(Peer):

    def __init__(self, parser):
        parser.add_argument("-v", "--player_port",
                            default=9999, type=int,
                            help="Port to listen to the player")

    def instance(self, args):
        Peer_DBS_video.player_port = args.player_port
        if args.set_of_rules == "DBS":
            peer = Peer_DBS("P", "Peer_DBS", args.loglevel)
        elif args.set_of_rules == "IMS":
            peer = Peer_IMS("P", "Peer_IMS", args.loglevel)
        
    def run(self, args):
        peer.chunks_before_leave = args.chunks_before_leave
        peer.set_splitter((args.splitter_address, args.splitter_port))
        peer.wait_for_the_player()
        peer.connect_to_the_splitter(peer_port=args.peer_port)
        peer.receive_public_endpoint()
        peer.receive_buffer_size()
        peer.receive_the_number_of_peers()
        peer.listen_to_the_team()
        peer.receive_the_list_of_peers()
        peer.send_ready_for_receiving_chunks()
        peer.send_peer_type()   # Only for simulation purpose
        peer.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    peer = Peer(parser)
    args = parser.parse_args()
    peer.instance(args)
    peer.run(args)


 
