import argparse
import logging
from core.splitter_dbs import Splitter_DBS
from core.splitter_dbs_video import Splitter_DBS_video
from splitter import Splitter

class Splitter_video(Splitter):

    def __init__(self):
        super().__init__()
        parser.add_argument("-c", "--channel",
                            defalut=Splitter_DBS_video.channel,
                            help="Channel (default={})"
                            .format(Splitter_DBS_video))
        #args = parser.parse_args()

    def instance(self):
        if args.set_of_rules == "DBS" or args.set_of_rules == "IMS":
            splitter = Splitter_DBS_video("Splitter_DBS")
        if __debug__:
            lg = logging.getLogger("Splitter_DBS")
            lg.setLevel(args.loglevel)

if __name__ == "__main__":
    splitter = Splitter_video()
    splitter.instance()
    splitter.run()
