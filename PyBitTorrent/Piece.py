from typing import List, Union

from PyBitTorrent.Block import Block, BlockStatus, create_blocks
from PyBitTorrent.Exceptions import PieceIsPending, PieceIsFull


class Piece:
    def __init__(self, index, size):
        self.index = index
        self.size = size
        self.blocks: List[Block] = create_blocks(self.size)

    def __str__(self):
        return f'[{self.index}]'

    def is_full(self):
        for block in self.blocks:
            if block.status != BlockStatus.FULL:
                return False

        return True

    def get_free_block(self) -> Union[Block, None]:
        for block in self.blocks:
            block.calculate_status()
            if block.status == BlockStatus.FREE:
                return block

        if self.is_full():
            raise PieceIsFull
        else:
            raise PieceIsPending

    def get_block_by_offset(self, offset):
        for block in self.blocks:
            if block.offset == offset:
                return block

        raise PieceIsPending

    def get_data(self):
        data = b''
        for block in self.blocks:
            data += block.data

        return data


def create_pieces(file_size, piece_size) -> List[Piece]:
    pieces: List[Piece] = []
    pieces_amount = int(file_size / piece_size)

    # Generate pieces
    for i in range(pieces_amount):
        piece = Piece(i, piece_size)
        pieces.append(piece)

    last_piece_size = file_size % piece_size

    if last_piece_size:
        last_piece = Piece(pieces_amount, last_piece_size)
        pieces.append(last_piece)

    return pieces
