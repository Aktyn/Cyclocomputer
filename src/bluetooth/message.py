STAMP = bytes('mgdlnkczmr', 'ascii')


def is_stamp(data: bytes):
    if len(data) != len(STAMP):
        return False
    for i in range(len(STAMP)):
        if data[i] != STAMP[i]:
            return False
    return True


class Message:
    REQUEST_SETTINGS = 0x01
    CURRENT_SPEED = 0x02
