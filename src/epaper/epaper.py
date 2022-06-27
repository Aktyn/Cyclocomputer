from src.common.utils import mock_epaper
from src.epaper.common import bits_order_reverse_lut, reverse_bytearray

if not mock_epaper():
    import framebuf
    from src.epaper.images import Images
    from src.epaper.epd_2in9 import EPD_2in9
    from src.epaper.font import Font


    class Epaper:
        __line_height = 10
        __char_width = 8
        __static_area_height = 40  # It leaves 256 px of screen height

        def __init__(self):
            self.__epd = EPD_2in9()

            self.__buffers: dict[str, bytearray] = {}
            self.__frame_buffers: dict[str, framebuf.FrameBuffer] = {}
            self.__prepare()

            # self.__epd.init()
            # self.__epd.clear(0xff)

        def close(self):
            self.__epd.sleep()

        def restart(self):
            self.__epd.sleep()
            self.__epd = EPD_2in9()

        @property
        def width(self):
            return self.__epd.width

        @property
        def height(self):
            return self.__epd.height

        def __prepare(self):
            self.__buffers['logo'] = bytearray([0xff] * (self.__epd.height * self.__epd.width // 8))
            offset_top = (self.__epd.height // 2) * self.__epd.width // 8
            for index in range(len(Images.LOGO_BUFFER)):
                bit = Images.LOGO_BUFFER[len(Images.LOGO_BUFFER) - 1 - index]
                self.__buffers['logo'][index + offset_top] = bits_order_reverse_lut[bit]

            self.__fonts = {
                'temperature_40px': Font(Images.TEMPERATURE_40PX, 128, 128, Images.TEMPERATURE_40PX_GLYPHS, 40),
                'digits_104px': Font(Images.DIGITS_104PX, 256, 256, Images.DIGITS_104PX_GLYPHS, 104),
            }

            self.__buffers['static_area'] = bytearray([0xff] * (self.__epd.height * self.__epd.width // 8))
            self.__frame_buffers['static_area'] = framebuf.FrameBuffer(
                self.__buffers['static_area'], self.__epd.width, self.__epd.height, framebuf.MONO_HLSB
            )

            self.__buffers['real_time_data'] = bytearray(
                [0xff] * ((self.__epd.height - Epaper.__static_area_height) * self.__epd.width // 8)
            )
            self.__frame_buffers['real_time_data'] = framebuf.FrameBuffer(
                self.__buffers['real_time_data'],
                self.__epd.width, self.__epd.height - Epaper.__static_area_height,
                framebuf.MONO_HLSB
            )

        def clear(self, init_only=False):
            self.__epd.init()
            if not init_only:
                self.__epd.clear(0xff)

        def draw_text(self, text: str, y: int):
            lines = text.split('\n')
            buffer_name = f'text_line_{len(lines)}'
            if buffer_name not in self.__buffers:
                height = Epaper.__line_height * len(lines)
                self.__buffers[buffer_name] = bytearray([0xff] * (height * self.__epd.width // 8))
                self.__frame_buffers[buffer_name] = framebuf.FrameBuffer(
                    self.__buffers[buffer_name], self.__epd.width, height, framebuf.MONO_HLSB
                )

            self.__frame_buffers[buffer_name].fill(0xff)
            for line_index, line in enumerate(lines):
                text_length = len(line) * Epaper.__char_width
                self.__frame_buffers[buffer_name].text(
                    line, (self.__epd.width - text_length) // 2, line_index * Epaper.__line_height, 0x00
                )
            self.__epd.display_partial(
                reverse_bytearray(self.__buffers[buffer_name]),
                0, y - (len(lines) - 1) * Epaper.__line_height,
                self.__epd.width, Epaper.__line_height * len(lines)
            )

        def draw_logo(self):
            self.__epd.display_base(self.__buffers['logo'])

        def draw_static_area(self, temperature: float):
            self.__frame_buffers['static_area'].fill_rect(
                0, (self.__epd.height - Epaper.__static_area_height),
                self.__epd.width, Epaper.__static_area_height,
                0xff
            )

            self.__fonts['temperature_40px'].draw(
                f'{round(temperature)}°C',
                self.__frame_buffers['static_area'], self.__epd.width, self.__epd.height,
                # 5 pixels of manual offset to make the text better centered vertically
                0, self.__static_area_height - 5
            )

            self.__epd.display_base(self.__buffers['static_area'])

        def draw_speed(self, speed: float, refresh_only_speed_area=False):
            area_height = (self.__epd.height - Epaper.__static_area_height) // 2
            self.__frame_buffers['real_time_data'].fill_rect(
                0, 0 if refresh_only_speed_area else area_height,
                self.__epd.width, area_height, 0xff
            )

            # TODO: test speed of it
            self.__fonts['digits_104px'].draw(
                f'{round(speed)}',
                self.__frame_buffers['real_time_data'],
                self.__epd.width,
                area_height if refresh_only_speed_area else self.__epd.height - Epaper.__static_area_height,
                # 22 pixels of manual offset to make the digits better centered vertically
                0,
                area_height - 22 if refresh_only_speed_area else area_height - 22
            )

            if refresh_only_speed_area:
                self.__epd.display_partial(
                    self.__buffers['real_time_data'],
                    0, area_height,
                    self.__epd.width, area_height
                )
            else:
                self.__epd.display_partial(
                    self.__buffers['real_time_data'],
                    0, 0,
                    self.__epd.width, self.__epd.height - Epaper.__static_area_height
                )

else:
    class Epaper:
        def __init__(self):
            pass
