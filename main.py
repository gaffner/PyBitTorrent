import logging
from argparse import ArgumentParser, FileType, ArgumentDefaultsHelpFormatter

from Bittorrent import BitTorrentClient

LOGGING_NONE = 100


def main():
    """
    Script for downloading torrent files
    """

    parser = ArgumentParser(main.__doc__, formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--torrent', type=FileType('rb'), help='Path of the Torrent file', required=True)
    parser.add_argument('--peers', type=FileType('rb'), help='Path to file contain peers (in the format:'
                                                             'ip:port for each line)')
    parser.add_argument('--no-progress-bar', action='store_true', default=False, help='should show progress bar')
    parser.add_argument('--max-peers', type=int, default=12, help='Max connected peers')
    args = parser.parse_args()

    # init logger and argument parser
    logging_level = LOGGING_NONE
    if args.no_progress_bar:
        logging_level = logging.DEBUG


    logging.basicConfig(level=logging_level,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                        )

    # Create client from the BitTorrent Meta File
    torrentClient = BitTorrentClient(torrent=args.torrent, max_peers=args.max_peers,
                                     no_progress_bar=args.no_progress_bar, peers_file=args.peers)

    # Start downloading the file
    torrentClient.start()


if __name__ == '__main__':
    main()
