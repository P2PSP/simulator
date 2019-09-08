"""
@package simulator
chunk_structure module
"""

# Positions of each field (chunk, chunk_number, origin, etc.) in a
# buffer's cell.

class ChunkStructure:
    CHUNK_NUMBER = 0
    CHUNK_DATA   = 1
    ORIGIN       = 2  # (IP_address, port)
#   TIMESTAMP    = 3
