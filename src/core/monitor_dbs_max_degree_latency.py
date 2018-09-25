"""
@package simulator
peer_dbs_max_degree_latency module
"""

from .monitor_dbs_latency import Monitor_DBS_latency
from .monitor_dbs_max_degree import Monitor_DBS_max_degree

class Monitor_DBS_max_degree_latency(Monitor_DBS_latency, Monitor_DBS_max_degree):
    pass
