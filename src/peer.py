import argparse
import logging
from core.peer_dbs import Peer_DBS
from core.peer_ims import Peer_IMS

class Peer():

    def add_args(self, parser):
        parser.add_argument("-s", "--set_of_rules", default="ims", help="set of rules")
        parser.add_argument("-a", "--splitter_address", default="127.0.1.1", help="Splitter address")
        parser.add_argument("-p", "--splitter_port", default=Peer_DBS.splitter[1], type=int, help="Splitter port")
        parser.add_argument("-m", "--peer_port", default=0, type=int, help="Peer port (default={})".format(Peer_DBS.peer_port))
        if __debug__:
            parser.add_argument("--loglevel", default=logging.ERROR, help="Log level (default={})".format(logging.getLevelName(logging.ERROR)))
            logging.basicConfig(format="%(message)s - %(asctime)s - %(name)s - %(levelname)s")

    def instance(self, args):
        Peer_DBS.peer_port = args.peer_port
        Peer_DBS.splitter = (args.splitter_address, args.splitter_port)
        if args.set_of_rules == "DBS":
            self.peer = Peer_DBS("P", "Peer_DBS", args.loglevel)
        else:
            self.peer = Peer_IMS("P", "Peer_IMS", args.loglevel)

    def run(self, args):
        self.peer.connect_to_the_splitter(peer_port=args.peer_port)
        self.peer.receive_public_endpoint()
        self.peer.receive_buffer_size()
        self.peer.receive_the_number_of_peers()
        self.peer.listen_to_the_team()
        self.peer.receive_the_list_of_peers()
        self.peer.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    peer = Peer()
    peer.add_args(parser)
    args = parser.parse_args()
    peer.instance(args)
    peer.run(args)


 
