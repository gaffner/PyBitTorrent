from Message import Message, Handshake


class MessageFactory:
    @staticmethod
    def create_message(payload) -> Message:
        _id = payload[0]
        return messages_creators[_id](payload)

    @staticmethod
    def create_handshake_message(payload):
        return Handshake.from_bytes(payload)

    @staticmethod
    def create_piece_message(payload) -> Message:
        pass

    @staticmethod
    def create_request_message(payload) -> Message:
        pass


messages_creators = {1: MessageFactory.create_piece_message,
                     2: MessageFactory.create_request_message}
