"""
@package simulator
chunk_structure module
"""

# Positions of each field (chunk, chunk_number, origin, etc.) in a
# buffer's cell.

class ChunkStructure:
    CHUNK_NUMBER = 0
    CHUNK_DATA   = 1
    ORIGIN_ADDR  = 2
    ORIGIN_PORT  = 3
    HOPS         = 4  # Simulator only
    TIME         = 5  # Simulator only
