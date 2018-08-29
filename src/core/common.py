"""
@package simulator
common module
"""

class Common:
    MAX_CHUNK_NUMBER = 65536  # 65535? 32767?.
    COUNTERS_TIMING = 1  # In seconds.
    BUFFER_SIZE = 128  # In chunks.
    MAX_CHUNK_LOSS = 16  # In chunks.
    CHUNK_CADENCE = 0.01 # In seconds

    # Control messages transmitted between peers (the messages
    # interchanged with the slitter are excluded of this list):
    HELLO = -1  # Sent to me your chunks (received from the splitter)
    GOODBYE = -2  # See you later.
    REQUEST = -3  # Send to me the chunks originated at ...
    PRUNE = -4  # Don't send to me chunks originated at ...
    LOST_CHUNK = -5 # I have lost the chunk number ...
