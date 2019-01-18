"""
@package simulator
common module
"""

import logging


class Common:
    loglevel = logging.ERROR

    MAX_CHUNK_NUMBER = 65536  # 65535? 32767?.
    COUNTERS_TIMING = 1  # In seconds.
    MAX_CHUNK_LOSS = 8  # In chunks.
    CHUNK_CADENCE = 0.1  # In seconds

    # Control messages transmitted between peers (the messages
    # interchanged with the slitter are excluded of this list):
    HELLO = -1  # Sent to me your chunks (received from the splitter)
    GOODBYE = -2  # See you later.
    REQUEST = -3  # Send to me the chunks originated at ...
    PRUNE = -4  # Don't send to me chunks originated at ...
    LOST_CHUNK = -5  # I have lost the chunk number ...

    # Positions of each field (chunk, chunk_number, origin) in a
    # buffer's message.
    CHUNK_NUMBER = 0
    CHUNK_DATA = 1
    ORIGIN = 2
