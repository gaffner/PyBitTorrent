from io import BytesIO, SEEK_CUR
from string import digits
from typing import List, Dict, Union
import functools

END_CHAR = b'e'


def get_int(data: BytesIO, end=END_CHAR) -> int:
    """
    Read until reach the int end char
    """
    value = ''
    byte = data.read(1)  # we need the first number of length

    while byte != end:
        if byte == end:
            break

        value += byte.decode()
        byte = data.read(1)

    return int(value)


def get_string(data: BytesIO) -> bytes:
    """
    Read the length of the string,
    And then read this amount of bytes
    """
    data.seek(-1, SEEK_CUR)
    length = get_int(data, b':')
    value = data.read(length)
    try:
        value = value.decode()
    except UnicodeDecodeError:
        pass

    return value


def get_dict(data) -> Dict:
    """
    Read the first key, and then
    iterate over the all the dictionary.
    """
    key: bytes = bdecode(data)
    dictionary = {}
    while key:
        value = bdecode(data)
        dictionary[key] = value

        key = bdecode(data)

    return dictionary


def get_list(data):
    """
    Read the first value, then
    iterate over all the list values
    """
    values = []
    value = bdecode(data)
    while value:
        values.append(value)
        value = bdecode(data)

    return values


TYPES = {
    b'i': get_int,
    b'd': get_dict,
    b'l': get_list
}
TYPES.update({digit.encode(): get_string for digit in digits})


def bdecode(data: bytes) -> Union[bytes, int, Dict, List]:
    # For the user call
    if isinstance(data, bytes):
        data = BytesIO(data)

    first_char = data.read(1)
    if first_char == END_CHAR:
        return None

    decoder = TYPES[first_char]
    value = decoder(data)
    return value


# Encoders
def with_end(func):
    def inner(*args, **kwargs):
        func(*args, **kwargs)
        stream = args[1]
        stream.write(END_CHAR)

    return inner


def encode_buffer(data: Union[bytes, str], stream):
    if type(data) is str:
        data = data.encode()

    stream.write(str(len(data)).encode())  # Write buffer length
    stream.write(':'.encode())  # String seperator
    stream.write(data)  # Write buffer itself


@with_end
def encode_int(data: int, stream: BytesIO):
    stream.write(f'i{str(data)}'.encode())


@with_end
def encode_list(data: List, stream: BytesIO):
    stream.write(b'l')
    for item in data:
        bencode(item, stream)


@with_end
def encode_dict(data: Dict, stream: BytesIO):
    stream.write(b'd')
    for key, value in data.items():
        bencode(key, stream)
        bencode(value, stream)


ENCODE_TYPES = {
    str: encode_buffer,
    bytes: encode_buffer,
    int: encode_int,
    list: encode_list,
    dict: encode_dict
}


def bencode(data, stream=None):
    if not stream:
        stream = BytesIO()

    ENCODE_TYPES[type(data)](data, stream)

    return stream.getvalue()
