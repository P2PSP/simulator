import argparse
import logging
from core.splitter_dbs import Splitter_DBS
from core.splitter_dbs_video import Splitter_DBS_video
from splitter import Splitter

class Splitter_video(Splitter):

    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument("-c", "--channel",
                            default=Splitter_DBS_video.channel,
                            help="Mount point of the channel in the (Icecast) server (default={})"
                            .format(Splitter_DBS_video.channel))
        parser.add_argument("-z", "--chunk_size",
                            default=Splitter_DBS_video.chunk_size,
                            help="Chunk size in bytes (default={})"
                            .format(Splitter_DBS_video.chunk_size))
        parser.add_argument("-e", "--header_chunks",
                            default=Splitter_DBS_video.header_chunks,
                            help="Header size in chunks (default={})"
                            .format(Splitter_DBS_video.header_chunks))
        parser.add_argument("-a", "--source_address",
                            default=Splitter_DBS_video.source_address,
                            help="Address of the source (default={})"
                            .format(Splitter_DBS_video.source_address))
        parser.add_argument("-t", "--source_port",
                            default=Splitter_DBS_video.source_port,
                            help="Listening port of the source (default={})"
                            .format(Splitter_DBS_video.source_port))

    def instance(self, args):
        if args.set_of_rules == "DBS" or args.set_of_rules == "IMS":
            Splitter_DBS_video.splitter_port = int(args.splitter_port)
            Splitter_DBS_video.max_chunk_loss = int(args.max_chunk_loss)
            Splitter_DBS_video.number_of_monitors = int(args.number_of_monitors)
            Splitter_DBS_video.buffer_size = int(args.buffer_size)
            Splitter_DBS_video.channel = args.channel
            Splitter_DBS_video.header_chunks = int(args.header_chunks)
            Splitter_DBS_video.source_address = args.source_address
            Splitter_DBS_video.source_port = int(args.source_port)
            self.splitter = Splitter_DBS_video("Splitter_DBS_video")
        if __debug__:
            lg = logging.getLogger("Splitter_DBS_video")
            lg.setLevel(args.loglevel)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    splitter = Splitter_video()
    splitter.add_args(parser)
    args = parser.parse_args()
    splitter.instance(args)
    splitter.run(args)
