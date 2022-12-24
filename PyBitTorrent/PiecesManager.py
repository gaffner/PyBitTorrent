import logging
import os
import tempfile
from PyBitTorrent import TorrentFile


class DiskManager:
    def __init__(self, output_directory: str, torrent: TorrentFile):
        self.output_directory = output_directory
        self.torrent = torrent
        self.written = 0
        self.multi_part = "files" in self.torrent.info.keys()
        if self.multi_part:
            self.file = tempfile.TemporaryFile()
        else:
            self.file = open(self.torrent.file_name, "wb")  # Regular one single file

    def write_piece(self, piece, piece_size):
        """
        Write piece to disk according to the offset
        """
        piece_data = piece.get_data()
        self.file.seek(piece_size * piece.index)
        self.file.write(piece_data)
        self.file.flush()

        self.written += 1

    def close(self):
        """
        Reorganize the pieces according to the
        Files structure specified in the torent file
        """
        # If torrent contain multiple file, split them
        if self.multi_part:
            self.file.seek(0)  # We start reading the file from the beginning
            for file in self.torrent.info['files']:
                # Calculate the full path of each file
                file_path = self.torrent.file_name  # We start from the directory name
                for entity in file['path']:
                    file_path = os.path.join(file_path, entity)

                logging.getLogger("BitTorrent").debug(f"Writing to file {file_path}")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Create directories if necessary
                logging.getLogger("BitTorrent").debug(f"Writing data in offsets {self.file.tell()}:{file['length']}")

                # Create the file and copy the data
                f = open(file_path, 'wb')
                file_data = self.file.read(file['length'])
                f.write(file_data)
                f.close()

        self.file.close()
