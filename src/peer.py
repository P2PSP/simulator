import argparse
import logging
from core.peer_dbs import Peer_DBS


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--set-of-rules",
                        help="set of rules")
    parser.add_argument("-a", "--splitter-address",
                        help="Splitter address")
    parser.add_argument("-p", "--splitter-port", type=int,
                        help="Splitter port")
    parser.add_argument("-l", "--chunks-before-leave", type=int,
                        help="Number of chunk before leave the team")
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if args.set_of_rules == "dbs":
        peer = Peer_DBS("P")
    # elif self.set_of_rules == "ims":
        # splitter = Splitter_IMS()

    peer.chunks_before_leave = args.chunks_before_leave
    peer.set_splitter((args.splitter_address, args.splitter_port))
    peer.connect_to_the_splitter()
    peer.receive_buffer_size()
    peer.receive_the_number_of_peers()
    peer.listen_to_the_team()
    peer.receive_the_list_of_peers()
    peer.send_ready_for_receiving_chunks()
    peer.send_peer_type()   # Only for simulation purpose
    peer.run()
