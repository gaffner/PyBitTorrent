import logging
import random
from typing import Dict, List

from Message import Request, Piece, BitField
from Peer import Peer


class PiecesManager:
    def __init__(self, file_size: int, piece_length: int, peers: List[Peer]):
        self.piece_length = piece_length
        self.max_pieces = int(file_size / piece_length)
        self.pieces: Dict[Peer, List[int]] = {}
        self.pieces_have: List[int] = []
        # TODO: check if block size is smaller then 32KB.
        #  if yes - decrease it and write mechanism that ask for specific block
        logging.getLogger('BitTorrent').info(f"Block size set to {self.piece_length}")

        for peer in peers:
            self.pieces[peer] = []

    def handle_bitfield(self, peer: Peer, bitfieldMessage: BitField):
        """
        Function will add the piece the peer have
        to the piece map according to the given bitfield.
        """
        bitfield = bitfieldMessage.bitfield
        for index, piece_exists in enumerate(bitfield):
            if index > self.max_pieces:  # Reached the padding bits
                break

            if piece_exists and index not in self.pieces[peer]:
                self.pieces[peer].append(index)

        logging.getLogger('BitTorrent').info(f"Added bitfield of {peer}, total pieces of {len(bitfield)}")

    def request_piece(self):
        requested_piece = random.randint(0, self.max_pieces)
        while requested_piece in self.pieces_have:
            requested_piece = random.randint(0, self.max_pieces)  # I hate to write the same line twice...

        target_peers = []
        begin = 0

        logging.getLogger('BitTorrent').info(f"Requesting for piece {requested_piece}")

        # Check for each client if he have the piece
        for peer, pieces in self.pieces.items():
            if requested_piece in pieces:
                target_peers.append(peer)

        if len(target_peers) == 0:
            logging.getLogger('BitTorrent').info(f"Found no available clients")
            return

        request = Request(requested_piece, begin, self.piece_length)
        target_peer = random.choice(target_peers)

        target_peer.send_message(request)

    def write_block(self, piece: Piece):
        raise NotImplemented

    def read_block(self, index: int):
        raise NotImplemented
