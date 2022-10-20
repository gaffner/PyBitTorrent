import abc


class Tracker(abc.ABC):
    def __init__(self, url):
        self.url = url

    def get_peers(self):
        pass
