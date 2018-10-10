import argparse
import logging
from core.peer_dbs import Peer_DBS
from core.peer_dbs_video import Peer_DBS_video
from core.peer_ims import Peer_IMS
from peer import Peer

class Peer_video(Peer):

    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument("-v", "--player_port",
                            default=9999, type=int,
                            help="Port to listen to the player")

    def instance(self, args):
        Peer_DBS_video.player_port = args.player_port
        super().instance(args)
        
    def run(self, args):
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
    peer = Peer_video()
    peer.add_args(parser)
    args = parser.parse_args()
    peer.instance(args)
    peer.run(args)


 
