from typing import List
from urllib.parse import urlparse

from PyBitTorrent.Exceptions import UnknownTracker
from PyBitTorrent.HTTPTracker import HTTPTracker
from PyBitTorrent.Tracker import Tracker
from PyBitTorrent.UDPTracker import UDPTracker
from PyBitTorrent.Configuration import (
    TCP_ONLY
)


class TrackerFactory:
    @staticmethod
    def create_tracker(url: str):
        """
        Check the scheme of the url,
        and decide which type of tracker to create.
        :param url: url of the tracker (HTTP/UDP)
        :return: Tracker
        """
        parsed = urlparse(url)
        if "http" in parsed.scheme.lower():
            return HTTPTracker(url)
        elif "udp" in parsed.scheme.lower():
            if not TCP_ONLY :
                return UDPTracker(url)
        else:
            raise UnknownTracker(url)

    @staticmethod
    def create_trackers(urls: List[str]) -> List[Tracker]:
        """
        Create trackers from the given url list.
        Current options are HTTP/UDP.
        """
        trackers = []
        for url in urls:
            tracker = TrackerFactory.create_tracker(url[0])
            trackers.append(tracker)

        return trackers
