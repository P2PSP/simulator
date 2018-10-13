"""
@package simulator
monitor_dbs module
"""

from core.monitor_ims import Monitor_IMS
from core.peer_ims_simulator import Peer_IMS_simulator

class Monitor_IMS_simulator(Monitor_IMS, Peer_IMS_simulator):
    pass
