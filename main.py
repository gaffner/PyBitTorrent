import logging
import sys
from argparse import ArgumentParser, FileType

from bittorrent import BitTorrentClient


def main():
    """
    Script for downloading torrent files
    """
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                        )

    parser = ArgumentParser(main.__doc__)
    parser.add_argument('--torrent', nargs=1, type=FileType('rb'), help='Path of the Torrent file')
    args = parser.parse_args()
    print(args)

    torrentClient = BitTorrentClient(args.torrent[0])
    torrentClient.start()


if __name__ == '__main__':
    main()
