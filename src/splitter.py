import argparse
import logging
from core.splitter_dbs import Splitter_DBS
from core.common import Common

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--set-of-rules", default="dbs",
                        help="set of rules")
    parser.add_argument("-b", "--buffer-size", default=128, type=int,
                        help="Buffer size")
    parser.add_argument("-p", "--port", default=0, type=int,
                        help="Splitter port")
    parser.add_argument("--log", default=logging.ERROR, help="Log level")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    Common.BUFFER_SIZE = args.buffer_size

    if args.set_of_rules == "dbs" or args.set_of_rules == "ims":
        splitter = Splitter_DBS("Splitter_DBS")
    # elif self.set_of_rules == "ims":
        # splitter = Splitter_IMS()
    lg = logging.getLogger("Splitter_DBS")
    lg.setLevel(args.log)
    
    splitter.setup_peer_connection_socket(args.port)
    splitter.setup_team_socket()
    splitter_address = splitter.get_id()
    print("Splitter Address: {}".format(splitter_address))
    splitter.run()
