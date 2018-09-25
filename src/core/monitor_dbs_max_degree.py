"""
@package simulator
monitor_dbs_max_degree module
"""

from .peer_dbs_max_degree import Peer_DBS_max_degree
from .monitor_dbs import Monitor_DBS

class Monitor_DBS_max_degree(Peer_DBS_max_degree, Monitor_DBS):
    pass
