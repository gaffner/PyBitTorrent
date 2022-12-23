class DiskManager:
    def __init__(self, file_name: str):
        self.file = open(file_name, 'wb')
        self.written = 0

    def write_piece(self, piece, piece_size):
        piece_data = piece.get_data()
        self.file.seek(piece_size * piece.index)
        self.file.write(piece_data)
        self.file.flush()

        self.written += 1

    def close(self):
        print("\nClosing the file")
        self.file.close()
