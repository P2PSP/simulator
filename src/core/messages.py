"""
@package simulator
Message module
"""

# Control messages transmitted between peers (the messages
# interchanged with the slitter are excluded of this list).

class Messages:

    HELLO          = -1  # Sent to me your chunks (received from the splitter)
    GOODBYE        = -2  # See you later.
    REQUEST        = -3  # Send to me the chunks originated at ...
    PRUNE          = -4  # Don't send to me chunks originated at ...
    LOST_CHUNK     = -5  # I have lost the chunk number.
    REQUEST_ORIGIN = -6  # To request a new path from origin
