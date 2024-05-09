import hashlib
import logging
from copy import deepcopy

import rich
from PyBitTorrent.bcoder import bencode, bdecode
from PyBitTorrent.Exceptions import KeyNotFound


class TorrentFile:
    def __init__(self, torrent):
        """
        Initiate the TorrentFile object using the
        bcoder util that parse the .torrent file,
        and then calculate the sha1 value of the info dict.
        this important value will later use us in peer retrieve
        process and in the handshakes process.
        """
        logging.getLogger("BitTorrent").info("Start reading from BitTorrent file")
        with open(torrent, 'rb') as torrent_file:
            torrent_data = torrent_file.read()

        self.config = bdecode(torrent_data)
        self.info = self.config["info"]
        self.hash = hashlib.sha1(bencode(self.info)).digest()
        self.length = 0
        self.print_configuration()

        for key in [["name", "file_name"], ["piece length", "piece_size"]]:
            self._set_attribute_from_info(*key)

        # Calculate the total length
        if "files" in self.info.keys():
            for file in self.info["files"]:
                self.length += file["length"]
        else:
            self._set_attribute_from_info("length", "length")

    def print_configuration(self):
        """
        Help function for printing the configuration of
        the torrent file in an nice-to-look way using rich.
        """
        config = deepcopy(self.config)

        config["info"]["pieces"] = ""
        rich.print(config)

    def _set_attribute_from_info(self, key, self_key) :
        """
        Set value from info dict to self if exists
        else get the value from config
        """
        if key in self.info.keys() :
            self.__dict__[self_key] = self.info[key]
        elif key in self.config.keys() :
            self.__dict__[self_key] = self.config[key]
        else :
            raise KeyNotFound
