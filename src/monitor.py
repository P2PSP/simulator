import argparse
import logging
from core.monitor_dbs import Monitor_DBS
from core.monitor_ims import Monitor_IMS

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--chunks_before_leave", default=9999, type=int,
                        help="Number of chunk before leave the team")
    parser.add_argument("-s", "--set_of_rules", default="dbs",
                        help="set of rules")
    parser.add_argument("-a", "--splitter_address", default="127.0.1.1",
                        help="Splitter address")
    parser.add_argument("-p", "--splitter_port", default=4551, type=int,
                        help="Splitter port")
    parser.add_argument("-m", "--monitor_port", default=4552, type=int,
                        help="Monitor port")
    parser.add_argument("--loglevel", default=logging.ERROR, help="Log level")
    args = parser.parse_args()

    logging.basicConfig(format="%(message)s - %(asctime)s - %(name)s - %(levelname)s")

    if args.set_of_rules == "DBS":
        peer = Monitor_DBS("M", "Monitor_DBS", args.loglevel)
    elif args.set_of_rules == "IMS":
        peer = Monitor_IMS("M", "Monitor_IMS", args.loglevel)

    peer.chunks_before_leave = args.chunks_before_leave
    peer.set_splitter((args.splitter_address, args.splitter_port))
    peer.connect_to_the_splitter(args.monitor_port)
    peer.receive_public_endpoint()
    peer.receive_buffer_size()
    peer.receive_the_number_of_peers()
    peer.listen_to_the_team()
    peer.receive_the_list_of_peers()
    peer.send_ready_for_receiving_chunks()
    peer.send_peer_type()   # Only for simulation purpose
    peer.run()
