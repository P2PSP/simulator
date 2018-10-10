"""
@package simulator
monitor_ims_video module
"""

from .monitor_ims import Monitor_IMS
from .peer_ims_video import Peer_IMS_video

class Monitor_IMS_video(Monitor_IMS, Peer_IMS_video):
    pass
