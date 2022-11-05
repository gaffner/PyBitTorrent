from Message import MessageCode, Message, Handshake, UnknownMessage, KeepAlive, BitField


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


messages_creators = {MessageCode.BITFIELD: MessageFactory.create_bitfield_message}
