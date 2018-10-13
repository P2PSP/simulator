import argparse
import logging
from core.splitter_dbs import Splitter_DBS
from core.splitter_dbs_simulator import Splitter_DBS_simulator
from splitter import Splitter

class Splitter_simulator(Splitter):

    def instance(self, args):
        if args.set_of_rules == "DBS" or args.set_of_rules == "IMS":
            Splitter_DBS_simulator.splitter_port = args.splitter_port
            Splitter_DBS_simulator.max_chunk_loss = args.max_chunk_loss
            Splitter_DBS_simulator.number_of_monitors = args.number_of_monitors
            Splitter_DBS_simulator.buffer_size = args.buffer_size
            self.splitter = Splitter_DBS_simulator("Splitter_DBS_simulator")
        if __debug__:
            lg = logging.getLogger("Splitter_DBS_simulator")
            lg.setLevel(args.loglevel)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    splitter = Splitter_simulator()
    splitter.add_args(parser)
    args = parser.parse_args()
    splitter.instance(args)
    splitter.run(args)
