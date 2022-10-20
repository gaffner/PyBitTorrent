from urllib.parse import urlparse

from Exceptions import UnknownTracker
from HTTPTracker import HTTPTracker
from UDPTracker import UDPTracker
from Tracker import Tracker

from typing import List

class TrackerFactory:
    @staticmethod
    def create_tracker(url : str):
        """
        Check the scheme of the url,
        and decide which type of tracker to create.
        :param url: url of the tracker (HTTP/UDP)
        :return: Tracker
        """
        parsed = urlparse(url)
        if 'http' in parsed.scheme.lower():
            return HTTPTracker(url)
        elif 'udp' in parsed.scheme.lower():
            return UDPTracker(url)
        else:
            raise UnknownTracker(url)

    @staticmethod
    def create_trackers(urls: List[str]) -> List[Tracker]:
        trackers = []
        for url in urls:
            tracker = TrackerFactory.create_tracker(url[0])
            trackers.append(tracker)

        return trackers
