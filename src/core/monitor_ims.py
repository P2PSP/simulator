"""
@package simulator
monitor_dbs module
"""

from core.monitor_dbs import Monitor_DBS
from core.peer_ims import Peer_IMS


class Monitor_IMS(Monitor_DBS, Peer_IMS):
    pass
