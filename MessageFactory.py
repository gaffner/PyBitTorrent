from Message import Message, Handshake, UnknownMessage


class MessageFactory:
    @staticmethod
    def create_message(payload) -> Message:
        _id = payload[0]
        if _id not in messages_creators:
            return UnknownMessage(_id)

        return messages_creators[_id](payload)

    @staticmethod
    def create_handshake_message(payload):
        return Handshake.from_bytes(payload)



messages_creators = {}
