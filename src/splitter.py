import argparse
from core.splitter_dbs import Splitter_DBS
from core.common import Common


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--set-of-rules",
                        help="set of rules")
    parser.add_argument("-b", "--buffer-size", type=int,
                        help="Buffer size")
    args = parser.parse_args()

    Common.BUFFER_SIZE = args.buffer_size
    if args.set_of_rules == "dbs":
        splitter = Splitter_DBS()
    # elif self.set_of_rules == "ims":
        # splitter = Splitter_IMS()

    splitter.setup_peer_connection_socket()
    splitter.setup_team_socket()
    splitter_address = splitter.get_id()
    print("Splitter Address: {}".format(splitter_address))
    splitter.run()
