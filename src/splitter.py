import argparse
import logging
from core.splitter_dbs import Splitter_DBS
from core.common import Common

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--set_of_rules", default="dbs",
                        help="set of rules")
    parser.add_argument("-b", "--buffer_size", default=128, type=int,
                        help="Buffer size")
    parser.add_argument("-p", "--port", default=4551, type=int,
                        help="Splitter port")
    parser.add_argument("--loglevel", default=logging.ERROR, help="Log level")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    Common.BUFFER_SIZE = args.buffer_size

    if args.set_of_rules == "DBS" or args.set_of_rules == "IMS":
        splitter = Splitter_DBS("Splitter_DBS")
    # elif self.set_of_rules == "ims":
        # splitter = Splitter_IMS()
    lg = logging.getLogger("Splitter_DBS")
    lg.setLevel(args.loglevel)
    
    splitter.setup_peer_connection_socket(args.port)
    splitter.setup_team_socket()
    splitter_address = splitter.get_id()
    splitter.run()
