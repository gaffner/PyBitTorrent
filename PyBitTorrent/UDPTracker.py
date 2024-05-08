import logging
import socket
from typing import List
from urllib.parse import urlparse

from PyBitTorrent.Peer import Peer
from PyBitTorrent.TorrentFile import TorrentFile
from PyBitTorrent.Tracker import Tracker
from PyBitTorrent.UDPTrackerMessage import Connection, Announce, AnnounceResult
from PyBitTorrent.Configuration import (
    TIMEOUT,
    UDP_TRACKER_RECEIVE_SIZE
)


class UDPTracker(Tracker):

    def get_peers(self, peer_id: bytes, port: int, torrent: TorrentFile) -> List[Peer]:
        """
        Connect to udp tracker and retrieve from him list of peers. Following the
        BitTorrent UDP Tracker specification, And sourceforge unofficial guide:
        https://www.bittorrent.org/beps/bep_0015.html
        https://xbtt.sourceforge.net/udp_tracker_protocol.html
        """
        connection_id = 0x41727101980
        url_details = urlparse(self.url)
        tracker_address = (url_details.hostname, url_details.port)
        connection_request = Connection()

        try:
            # Send Connection Request
            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            sock.sendto(connection_request.to_bytes(), tracker_address)

            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(TIMEOUT)

            response = sock.recv(UDP_TRACKER_RECEIVE_SIZE)  # Answer should be 16 bytes

            connection_response = Connection.from_bytes(response)
            connection_id = connection_response.connection_id

            if connection_request != connection_response:
                logging.getLogger("BitTorrent").error(
                    "UDP Tracker request and response are not equal"
                )

            announce = Announce(
                connection_id, torrent.hash, peer_id, torrent.length, port
            )
            sock.sendto(announce.to_bytes(), tracker_address)

            response = sock.recv(UDP_TRACKER_RECEIVE_SIZE)  # Answer should be 98 bytes
            announce_response: AnnounceResult = AnnounceResult.from_bytes(response)

            if announce_response.transaction_id != announce.transaction_id:
                logging.getLogger("BitTorrent").error(
                    "UDP Tracker request and response are not equal"
                )

            peers = Tracker.extract_compact_peers(announce_response.peers)
            logging.getLogger("BitTorrent").info(
                f"success in scraping {self.url} got {len(peers)} peers"
            )
            return peers

        except socket.error:
            logging.getLogger("BitTorrent").error(
                f"Tracker {url_details.hostname}:{url_details.port} give no answer"
            )
            return []
