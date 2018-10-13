import argparse
from core.monitor_dbs import Monitor_DBS
from core.monitor_dbs_video import Monitor_DBS_video
from core.monitor_ims_video import Monitor_IMS_video
from monitor import Monitor

class Monitor_video(Monitor):

    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument("-v", "--player_port",
                            default=9999, type=int,
                            help="Port to listen to the player")

    def instance(self, args):
        Monitor_DBS.peer_port = args.peer_port
        Monitor_DBS.splitter = (args.splitter_address, args.splitter_port)
        Monitor_DBS.chunks_before_leave = args.chunks_before_leave
        Monitor_DBS_video.player_port = args.player_port
        if args.set_of_rules == "DBS":
            self.peer = Monitor_DBS_video("P", "Monitor_DBS", args.loglevel)
        else:
            self.peer = Monitor_IMS_video("P", "Monitor_IMS", args.loglevel)
        
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
        #self.peer.send_ready_for_receiving_chunks()
        self.peer.send_peer_type()   # Only for simulation purpose
        self.peer.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    peer = Monitor_video()
    peer.add_args(parser)
    args = parser.parse_args()
    peer.instance(args)
    peer.run(args)


 
