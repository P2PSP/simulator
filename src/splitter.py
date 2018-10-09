import argparse
import logging
from core.splitter_dbs import Splitter_DBS

class Splitter():

    def __init__(self, parser):
        parser.add_argument("-s", "--set_of_rules",
                            default="IMS",
                            help="Set of rules (default=\"IMS\")")
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

        if __debug__:
            parser.add_argument("--loglevel",
                                default=logging.ERROR,
                                help="Log level (default={})"
                                .format(logging.getLevelName(logging.ERROR)))
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def instance(self, args):
        if args.set_of_rules == "DBS" or args.set_of_rules == "IMS":
            Splitter_DBS.splitter_port = args.splitter_port
            Splitter_DBS.max_chunk_loss = args.max_chunk_loss
            Splitter_DBS.number_of_monitors = args.number_of_monitors
            Splitter_DBS.buffer_size = args.buffer_size
            splitter = Splitter_DBS("Splitter_DBS")
        if __debug__:
            lg = logging.getLogger("Splitter_DBS")
            lg.setLevel(args.loglevel)

    def run(self, args):
        splitter.setup_peer_connection_socket(args.splitter_port)
        splitter.setup_team_socket()
        splitter_address = splitter.get_id()
        splitter.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    splitter = Splitter(parser)
    args = parser.parse_args()
    splitter.instance(args)
    splitter.run(args)
