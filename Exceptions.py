class BasicException(Exception):
    pass


class UnknownTracker(BasicException):
    pass


class NotSupported(BasicException):
    pass


class PeerConnectionFailed(BasicException):
    pass


class PeerHandshakeFailed(BasicException):
    pass
