# from Exceptions import NotSupported
import logging

from Tracker import Tracker


class UDPTracker(Tracker):
    def get_peers(self):
        logging.getLogger('BitTorrent').error('No implementation to UDP tracker')
        # raise NotSupported

        return []
