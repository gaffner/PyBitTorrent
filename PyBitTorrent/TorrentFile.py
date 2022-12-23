import hashlib
import logging
from copy import deepcopy

import rich
from bcoding import bencode, bdecode


class TorrentFile:
    def __init__(self, torrent):
        """
        Initiate the TorrentFile object using the
        bcoding library that parse the .torrent file,
        and then calculate the sha1 value of the info dict.
        this important value will later use us in peer retrieve
        process and in the handshakes process.
        """
        logging.getLogger("BitTorrent").critical("Start reading from BitTorrent file")
        torrent_data = torrent.read()
        self.config = bdecode(torrent_data)
        self.info = self.config["info"]
        self.hash = hashlib.sha1(bencode(self.info)).digest()
        self.piece_size = self.config["info"]["piece length"]
        self.file_name = self.config["info"]["name"]
        self.length = 0
        self.print_configuration()
        torrent.close()

        # Calculate the total length
        if "files" in self.info.keys():
            for file in self.info["files"]:
                self.length += file["length"]
        else:
            self.length = self.info["length"]

    def print_configuration(self):
        """
        Help function for printing the configuration of
        the torrent file in an nice-to-look way using rich.
        """
        config = deepcopy(self.config)
        config["info"]["pieces"] = ""
        rich.print(config)
