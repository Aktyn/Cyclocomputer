STAMP = bytes('mgdlnkczmr', 'ascii')
IMAGE_DATA_PREFIX = bytes('<MAP_PREVIEW>', 'ascii')
IMAGE_DATA_SUFFIX = bytes('</MAP_PREVIEW>', 'ascii')


def is_stamp(data: bytes):
    if len(data) != len(STAMP):
        return False
    for i in range(len(STAMP)):
        if data[i] != STAMP[i]:
            return False
    return True


def is_correct_map_preview_data(data: bytes):
    pixels_size = (128 * 128 // 8)
    if len(data) != len(IMAGE_DATA_PREFIX) + pixels_size + len(IMAGE_DATA_SUFFIX):
        return False
    for i in range(len(IMAGE_DATA_PREFIX)):
        if data[i] != IMAGE_DATA_PREFIX[i]:
            return False
    for i in range(len(IMAGE_DATA_SUFFIX)):
        if data[len(IMAGE_DATA_PREFIX) + pixels_size + i] != IMAGE_DATA_SUFFIX[i]:
            return False
    return True


class Message:
    REQUEST_SETTINGS = 0x01
    UPDATE_SPEED = 0x02
    REQUEST_PROGRESS_DATA = 0x03
