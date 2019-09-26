import argparse
import logging

from core.splitter_dbs import Splitter_DBS

# Abstract class created only for minimizing the code of the
# inheritaged classes (Splitter_simulator and Splitter_video).

class Splitter():

    def add_args(self, parser):
        parser.add_argument("-s", "--set_of_rules",
                            default="DBS",
                            help="Set of rules (default=\"DBS\")")
        
        parser.add_argument("-b", "--buffer_size",
                            default=Splitter_DBS.buffer_size,
                            type=int,
                            help="Buffer size (default={})"
                            .format(Splitter_DBS.buffer_size))
        
        parser.add_argument("-p", "--splitter_port",
                            default=Splitter_DBS.splitter_port,
                            type=int,
                            help="Splitter port (default={})"
                            .format(Splitter_DBS.splitter_port))
        
        parser.add_argument("-l", "--max_chunk_loss",
                            default=Splitter_DBS.max_chunk_loss,
                            help="Maximum number of lost chunks per round (default={})"
                            .format(Splitter_DBS.max_chunk_loss))
        
        parser.add_argument("-n", "--number_of_monitors",
                            default=Splitter_DBS.number_of_monitors,
                            help="Number of monitors (default={})"
                            .format(Splitter_DBS.number_of_monitors))

    def instance(self, args):
        if args.set_of_rules == "DBS" or args.set_of_rules == "IMS":
            Splitter_DBS.splitter_port = int(args.splitter_port)
            Splitter_DBS.max_chunk_loss = int(args.max_chunk_loss)
            Splitter_DBS.number_of_monitors = int(args.number_of_monitors)
            Splitter_DBS.buffer_size = int(args.buffer_size)
            self.splitter = Splitter_DBS("Splitter_DBS")
        if __debug__:
            lg = logging.getLogger("Splitter_DBS")
            lg.setLevel(args.loglevel)

    def run(self, args):
        self.splitter.setup_peer_connection_socket(port=args.splitter_port)
        self.splitter.setup_team_socket()
        self.splitter_address = self.splitter.get_id()
        self.splitter.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    splitter = Splitter()
    splitter.add_args(parser)
    args = parser.parse_args()
    splitter.instance(args)
    splitter.run(args)
