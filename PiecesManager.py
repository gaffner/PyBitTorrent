from Piece import Piece


class PieceManager:
    def __init__(self, file_name: str):
        self.file = open(file_name, 'wb')

    def write_piece(self, piece):
        piece_data = piece.get_data()
        self.file.seek(piece.size * piece.index)
        self.file.write(piece_data)

