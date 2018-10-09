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
        if __debug__:
            parser.add_argument("--loglevel", default=logging.ERROR, help="Log level")
            logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def instance(self, args):
        if args.set_of_rules == "DBS" or args.set_of_rules == "IMS":
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
