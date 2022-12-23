from PyBitTorrent.Message import MessageCode, Message, Handshake, \
    UnknownMessage, KeepAlive, BitField, Choke, Unchoke, PieceMessage, HaveMessage


class MessageFactory:
    @staticmethod
    def create_message(payload) -> Message:
        if len(payload) == 0:
            return KeepAlive()

        _id = payload[0]
        if _id not in messages_creators:
            return UnknownMessage(_id)

        return messages_creators[_id](payload[1:])  # Delete the message id byte

    @staticmethod
    def create_handshake_message(payload):
        return Handshake.from_bytes(payload)

    @staticmethod
    def create_bitfield_message(payload):
        return BitField.from_bytes(payload)

    @staticmethod
    def create_choke_message(payload):
        return Choke.from_bytes(payload)

    @staticmethod
    def create_unchoke_message(payload):
        return Unchoke.from_bytes(payload)

    @staticmethod
    def create_piece_message(payload):
        return PieceMessage.from_bytes(payload)

    @staticmethod
    def create_have_message(payload):
        return HaveMessage.from_bytes(payload)


messages_creators = {MessageCode.BITFIELD: MessageFactory.create_bitfield_message,
                     MessageCode.CHOKE: MessageFactory.create_choke_message,
                     MessageCode.UNCHOKE: MessageFactory.create_unchoke_message,
                     MessageCode.PIECE: MessageFactory.create_piece_message,
                     MessageCode.HAVE: MessageFactory.create_have_message}
