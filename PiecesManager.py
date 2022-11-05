import logging
import random
from typing import Dict, List

from bitstring import BitArray

from Message import Request, Piece, BitField
from Peer import Peer


class PiecesManager:
    def __init__(self, file_size: int, piece_length: int):
        self.piece_length = piece_length
        self.max_pieces = int(file_size / piece_length)
        self.pieces_map: Dict[int, List[Peer]] = {}
        # TODO: check if block size is smaller then 32KB.
        #  if yes - decrease it and write mechanism that ask for specific block
        logging.getLogger('BitTorrent').info(f"Block size set to {self.piece_length}")

        self.pieces_map = dict(zip(range(self.max_pieces+1), [[] for _ in range(self.max_pieces+1)]))

    def handle_bitfield(self, peer: Peer, bitfieldMessage: BitField):
        """
        Function will add the piece the peer have
        to the piece map according to the given bitfield.
        """
        bitfield = bitfieldMessage.bitfield
        for index, piece_exists in enumerate(bitfield):
            if index > self.max_pieces:  # Reached the padding bits
                break

            if piece_exists:
                self.pieces_map[index].append(peer)

        logging.getLogger('BitTorrent').info(f"Added bitfield of {peer}, total pieces of {len(bitfield)}")

    def update_piece_map(self, peer: Peer, pieces: List[int]):
        logging.getLogger('BitTorrent').info(f"Updating piece map of peer {peer}")
        for piece in pieces:
            if piece <= self.max_pieces:
                self.pieces_map[piece].append(peer)
            else:
                logging.getLogger('BitTorrent').error(f"Found too big block: {piece}")

    def request_piece(self):
        piece_index = random.choice(list(self.pieces_map.keys()))
        begin = 0

        if piece_index in self.pieces_map:
            request = Request(piece_index, begin, self.piece_length)
            peers = self.pieces_map[piece_index]  # Retrieve all the peers have this piece
            peer = random.choice(peers)  # Choose random client
            peer.send_message(request)  # Send the request message

    def write_block(self, piece: Piece):
        raise NotImplemented

    def read_block(self, index: int):
        raise NotImplemented
