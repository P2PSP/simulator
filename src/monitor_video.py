import argparse
from core.monitor_dbs import Monitor_DBS
from core.monitor_dbs_video import Monitor_DBS_video
from core.monitor_ims_video import Monitor_IMS_video
from monitor import Monitor
from peer_video import Peer_video

class Monitor_video(Monitor, Peer_video):

    def add_args(self, parser):
        Peer_video().add_args(parser)
        
    def instance(self, args):
        Monitor_DBS.peer_port = args.peer_port
        Monitor_DBS.splitter = (args.splitter_address, args.splitter_port)
        Monitor_DBS.player_port = args.player_port
        if args.set_of_rules == "DBS":
            self.peer = Monitor_DBS_video("P", "Monitor_DBS_video", args.loglevel)
        else:
            self.peer = Monitor_IMS_video("P", "Monitor_IMS_video", args.loglevel)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    peer = Monitor_video()
    peer.add_args(parser)
    args = parser.parse_args()
    peer.instance(args)
    peer.run(args)
