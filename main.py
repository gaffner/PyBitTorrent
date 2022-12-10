import logging
from argparse import ArgumentParser, FileType

from Bittorrent import BitTorrentClient


def main():
    """
    Script for downloading torrent files
    """
    # init logger and argument parser
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                        )

    parser = ArgumentParser(main.__doc__)
    parser.add_argument('--torrent', nargs=1, type=FileType('rb'), help='Path of the Torrent file')
    args = parser.parse_args()

    # Create client from the BitTorrent Meta File
    torrent_file = args.torrent[0]

    torrentClient = BitTorrentClient(torrent_file)  # 'peers.txt' Read peers from file mode
    # torrentClient = BitTorrentClient(torrent_file, 'peers.txt')  # Read peers from file mode
    torrentClient.start()


if __name__ == '__main__':
    main()
