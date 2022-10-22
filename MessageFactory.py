from Message import Message


class MessageFactory:
    @staticmethod
    def create_message(data) -> Message:
        _id = data[0]
        return messages_creators[_id](data)

    @staticmethod
    def create_piece_message(data) -> Message:
        pass

    @staticmethod
    def create_request_message(data) -> Message:
        pass


messages_creators = {1: MessageFactory.create_piece_message,
                     2: MessageFactory.create_request_message}
