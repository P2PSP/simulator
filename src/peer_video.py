import argparse
from core.peer_dbs import Peer_DBS
from core.peer_dbs_video import Peer_DBS_video
from core.peer_ims_video import Peer_IMS_video
from peer import Peer

class Peer_video(Peer):

    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument("-v", "--player_port",
                            default=9999, type=int,
                            help="Port to listen to the player")

    def instance(self, args):
        Peer_DBS.peer_port = args.peer_port
        Peer_DBS.splitter = (args.splitter_address, args.splitter_port)
        Peer_DBS.chunks_before_leave = args.chunks_before_leave
        Peer_DBS_video.player_port = args.player_port
        if args.set_of_rules == "DBS":
            self.peer = Peer_DBS_video("P", "Peer_DBS", args.loglevel)
        else:
            self.peer = Peer_IMS_video("P", "Peer_IMS", args.loglevel)
        
    def run(self, args):
        self.peer.wait_for_the_player()
        self.peer.connect_to_the_splitter(peer_port=args.peer_port)
        #self.peer.receive_the_header()
        self.peer.receive_chunk_size()
        self.peer.receive_public_endpoint()
        self.peer.receive_buffer_size()
        self.peer.receive_the_number_of_peers()
        self.peer.listen_to_the_team()
        self.peer.receive_the_list_of_peers()
        self.peer.send_ready_for_receiving_chunks()
        self.peer.send_peer_type()   # Only for simulation purpose
        self.peer.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    peer = Peer_video()
    peer.add_args(parser)
    args = parser.parse_args()
    peer.instance(args)
    peer.run(args)


 
