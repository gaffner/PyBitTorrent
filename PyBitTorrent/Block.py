import time
from enum import Enum
from typing import List


class BlockStatus(Enum):
    FREE = 1
    REQUESTED = 2
    FULL = 3


class Block:
    default_size = 16384
    max_waiting_time = 7

    def __init__(self, offset, size=default_size):
        self.status = BlockStatus.FREE
        self.offset = offset
        self.size = size
        self.data = b""
        self.time_requested = 0  # Used for determine block status

    def set_requested(self):
        self.time_requested = time.time()
        self.status = BlockStatus.REQUESTED

    def calculate_status(self):
        """
        Check if the block status should change from
        REQUESTED to FREE if the max waiting time passed.
        """
        if self.status == BlockStatus.REQUESTED:
            duration_waited = time.time() - self.time_requested
            if duration_waited > Block.max_waiting_time:
                self.status = BlockStatus.FREE


def create_blocks(piece_size) -> List[Block]:
    """
    Create blocks according to blocks_length parameter
    """
    blocks: List[Block] = []
    blocks_amount = int(piece_size / Block.default_size)
    for i in range(blocks_amount):
        block = Block(i * Block.default_size)
        blocks.append(block)

    # Check if there is left over bytes
    last_block_size = piece_size % Block.default_size

    # The size of the last block will be the left over
    if last_block_size:
        last_block = Block(blocks_amount * Block.default_size, last_block_size)
        blocks.append(last_block)

    return blocks
