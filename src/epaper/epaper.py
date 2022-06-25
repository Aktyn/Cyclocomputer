import sys
import time

from src.common.utils import mock_epaper

if not mock_epaper():
    import framebuf
    from src.epaper.images import Images
    from src.epaper.epd_2in9 import EPD_2in9


    class Epaper:
        __bits_order_reverse_lut = [0, 128, 64, 192, 32, 160, 96, 224, 16, 144, 80, 208, 48, 176, 112, 240,
                                    8, 136, 72, 200, 40, 168, 104, 232, 24, 152, 88, 216, 56, 184, 120,
                                    248, 4, 132, 68, 196, 36, 164, 100, 228, 20, 148, 84, 212, 52, 180,
                                    116, 244, 12, 140, 76, 204, 44, 172, 108, 236, 28, 156, 92, 220, 60,
                                    188, 124, 252, 2, 130, 66, 194, 34, 162, 98, 226, 18, 146, 82, 210, 50,
                                    178, 114, 242, 10, 138, 74, 202, 42, 170, 106, 234, 26, 154, 90, 218,
                                    58, 186, 122, 250, 6, 134, 70, 198, 38, 166, 102, 230, 22, 150, 86, 214,
                                    54, 182, 118, 246, 14, 142, 78, 206, 46, 174, 110, 238, 30, 158, 94,
                                    222, 62, 190, 126, 254, 1, 129, 65, 193, 33, 161, 97, 225, 17, 145, 81,
                                    209, 49, 177, 113, 241, 9, 137, 73, 201, 41, 169, 105, 233, 25, 153, 89,
                                    217, 57, 185, 121, 249, 5, 133, 69, 197, 37, 165, 101, 229, 21, 149, 85,
                                    213, 53, 181, 117, 245, 13, 141, 77, 205, 45, 173, 109, 237, 29, 157,
                                    93, 221, 61, 189, 125, 253, 3, 131, 67, 195, 35, 163, 99, 227, 19, 147,
                                    83, 211, 51, 179, 115, 243, 11, 139, 75, 203, 43, 171, 107, 235, 27,
                                    155, 91, 219, 59, 187, 123, 251, 7, 135, 71, 199, 39, 167, 103, 231, 23,
                                    151, 87, 215, 55, 183, 119, 247, 15, 143, 79, 207, 47, 175, 111, 239,
                                    31, 159, 95, 223, 63, 191, 127, 255]
        __line_height = 10
        __char_width = 8

        def __init__(self):
            self.__epd = EPD_2in9()
            # self.__epd.clear(0xff)  # unnecessary

            self.__buffers: dict[str, bytearray] = {}
            self.__frame_buffers: dict[str, framebuf.FrameBuffer] = {}
            self.__prepare()
            # self.__prepare_for_fast_refresh()

            # self.__epd.init()
            # self.__epd.clear(0xff)

        def close(self):
            self.__epd.sleep()

        @property
        def width(self):
            return self.__epd.width

        @property
        def height(self):
            return self.__epd.height

        def __prepare(self):
            self.__buffers['logo'] = bytearray([0xff] * (self.__epd.height * self.__epd.width // 8))
            offset_top = (self.__epd.height // 2 - 64 + 32) * self.__epd.width // 8
            for index in range(len(Images.LOGO_BUFFER)):
                bit = Images.LOGO_BUFFER[len(Images.LOGO_BUFFER) - 1 - index]
                self.__buffers['logo'][index + offset_top] = Epaper.__bits_order_reverse_lut[bit]

        def clear(self):
            self.__epd.init()
            self.__epd.clear(0xff)

        # def __prepare_for_fast_refresh(self):
        #     self.__epd.display_base(bytearray([0xff] * (self.__epd.height * self.__epd.width // 8)))

        def draw_line(self, text: str, y: int):
            lines = text.split('\n')
            buffer_name = f'text_line_{len(lines)}'
            if buffer_name not in self.__buffers:
                self.__buffers[buffer_name] = bytearray(
                    [0xff] * (Epaper.__line_height * len(lines) * self.__epd.width // 8)
                )
                self.__frame_buffers[buffer_name] = framebuf.FrameBuffer(
                    self.__buffers[buffer_name], self.__epd.width, Epaper.__line_height * len(lines), framebuf.MONO_HLSB
                )

            self.__frame_buffers[buffer_name].fill(0xff)
            for line_index, line in enumerate(lines):
                text_length = len(line) * Epaper.__char_width
                self.__frame_buffers[buffer_name].text(
                    line, (self.__epd.width - text_length) // 2, line_index * Epaper.__line_height, 0x00
                )
            self.__epd.display_partial(self.__reverse_bytearray(self.__buffers[buffer_name]), 0,
                                       y - (len(lines) - 1) * Epaper.__line_height, self.__epd.width,
                                       Epaper.__line_height * len(lines))

        def draw_logo(self):
            self.__epd.display_base(self.__buffers['logo'])

        @staticmethod
        def __reverse_bytearray(array: bytearray):
            _reversed = bytearray(len(array))
            for i in range(len(array)):
                _reversed[i] = Epaper.__bits_order_reverse_lut[array[len(array) - i - 1]]
            return _reversed
else:
    class Epaper:
        def __init__(self):
            pass
