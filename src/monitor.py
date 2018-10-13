import argparse
import logging
from peer import Peer
from core.peer_dbs import Peer_DBS
from core.monitor_dbs import Monitor_DBS
from core.monitor_ims import Monitor_IMS

class Monitor(Peer):
    
    def add_args(self, parser):
        parser.add_argument("-l", "--chunks_before_leave", default=2000, type=int,
                            help="Number of chunk before leave the team")
        parser.add_argument("-s", "--set_of_rules", default="ims",
                            help="set of rules")
        parser.add_argument("-a", "--splitter_address", default="127.0.1.1",
                            help="Splitter address")
        parser.add_argument("-p", "--splitter_port",
                            default=Peer_DBS.splitter[1], type=int,
                            help="Splitter port (default={})"
                            .format(Peer_DBS.splitter[1]))
        parser.add_argument("-m", "--peer_port", default=0, type=int,
                            help="Monitor port (default={})".format(Peer_DBS.peer_port))
        if __debug__:
            parser.add_argument("--loglevel",
                                default=logging.ERROR,
                                help="Log level (default={})"
                                .format(logging.getLevelName(logging.ERROR)))
            logging.basicConfig(format="%(message)s - %(asctime)s - %(name)s - %(levelname)s")

    def instance(self, args):
        Peer_DBS.peer_port = args.peer_port
        Peer_DBS.splitter = (args.splitter_address, args.splitter_port)
        Peer_DBS.chunks_before_leave = args.chunks_before_leave
        if args.set_of_rules == "DBS":
            self.peer = Monitor_DBS("P", "Monitor_DBS", args.loglevel)
        else:
            self.peer = Monitor_IMS("P", "Monitor_IMS", args.loglevel)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    peer = Monitor()
    peer.add_args(parser)
    args = parser.parse_args()
    peer.instance(args)
    peer.run(args)
