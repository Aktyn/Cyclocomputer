from src.common.utils import mock_epaper, degrees_to_compass_direction
from src.epaper.common import bits_order_reverse_lut, reverse_bytearray

__arrows = ['⬆', '⬈', '➡', '⬊', '⬇', '⬋', '⬅', '⬉', '⬆']


def get_relative_wind_direction_arrow(heading: float, wind_direction: float):
    degrees = (wind_direction + 180) - heading

    attempt = 0
    while degrees < 0 and attempt < 64:
        degrees += 360
        attempt += 1
    index = (degrees % 360) / 45.0
    return __arrows[round(index)]


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
            for index in range(len(Images.AUTHOR_LOGO)):
                bit = Images.AUTHOR_LOGO[len(Images.AUTHOR_LOGO) - 1 - index]
                self.__buffers['logo'][index + offset_top] = bits_order_reverse_lut[bit]

            self.__fonts = {
                'common_24px': Font(Images.COMMON_24PX, 128, 128, Images.COMMON_24PX_GLYPHS, 24),
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

        def draw_static_area(self, temperature: float, wind_direction: float, wind_speed: float, city_name: str):
            self.__frame_buffers['static_area'].fill_rect(
                0, (self.__epd.height - Epaper.__static_area_height),
                self.__epd.width, Epaper.__static_area_height,
                0xff
            )

            max_chars = self.__epd.width // Epaper.__char_width
            if len(city_name) > max_chars:
                city_name = city_name[:max_chars - 3] + '...'
            self.__frame_buffers['static_area'].text(
                city_name,
                0, self.__epd.height - Epaper.__static_area_height + Epaper.__line_height * 2,
                0x00
            )

            wind_speed_text = f"{round(wind_speed, 1)}m/s"
            text_length = len(wind_speed_text) * Epaper.__char_width
            self.__frame_buffers['static_area'].text(
                wind_speed_text,
                self.__epd.width - text_length, self.__epd.height - Epaper.__static_area_height + Epaper.__line_height,
                0x00
            )

            wind_dir_text = degrees_to_compass_direction(wind_direction)
            text_length = len(wind_dir_text) * Epaper.__char_width
            self.__frame_buffers['static_area'].text(
                wind_dir_text,
                self.__epd.width - text_length, self.__epd.height - Epaper.__static_area_height,
                0x00
            )

            start = self.__epd.height - Epaper.__static_area_height
            self.__reverse_part_of_buffer('static_area', start, start + Epaper.__line_height * 3)

            self.__fonts['common_24px'].draw(
                f'{round(temperature)}°C',
                self.__frame_buffers['static_area'], self.__epd.width, self.__epd.height,
                0, 24,
                align=Font.ALIGN.LEFT
            )

            self.__epd.display_base(self.__buffers['static_area'])

        def draw_real_time_data(self,
                                speed: float,
                                gps_statistics: dict[str, float],
                                map_preview: bytes,
                                wind_direction: float,
                                bluetooth_connection_status: bool
                                ):
            area_height = (self.__epd.height - Epaper.__static_area_height) // 2
            self.__frame_buffers['real_time_data'].fill_rect(
                0, area_height,
                self.__epd.width, area_height, 0xff
            )

            self.__fonts['digits_104px'].draw(
                f'{round(speed)}',
                self.__frame_buffers['real_time_data'],
                self.__epd.width,
                self.__epd.height - Epaper.__static_area_height,
                0,
                84 + 4  # 84 is roughly maximum char height + manual offset for vertical centering
            )

            # NOTE: spaces before label are needed to align them in vertical axis
            gps_statistics_text = f"  Alt: {min(10000, max(-100, round(gps_statistics['altitude'])))}m"
            self.__frame_buffers['real_time_data'].text(
                gps_statistics_text, 0, area_height, 0x00
            )
            gps_statistics_text = f"Slope: {round(gps_statistics['slope'], 1)}"
            self.__frame_buffers['real_time_data'].text(
                gps_statistics_text, 0, area_height + Epaper.__line_height, 0x00
            )
            gps_statistics_text = f"  Dir: {degrees_to_compass_direction(gps_statistics['heading'])}"
            self.__frame_buffers['real_time_data'].text(
                gps_statistics_text, 0, area_height + Epaper.__line_height * 2, 0x00
            )

            text_height = Epaper.__line_height * 3  # line height multiplied by number of text lines
            self.__reverse_part_of_buffer('real_time_data', area_height, area_height + text_height)

            self.__fonts['common_24px'].draw(
                get_relative_wind_direction_arrow(gps_statistics['heading'], wind_direction),
                self.__frame_buffers['real_time_data'],
                self.__epd.width,
                self.__epd.height - Epaper.__static_area_height,
                self.__epd.width - 28,
                area_height,
                align=Font.ALIGN.LEFT
            )

            if bluetooth_connection_status is True:
                for i in range(len(map_preview)):
                    self.__buffers['real_time_data'][i] = map_preview[i]
            else:
                buffer_size = len(Images.BLUETOOTH_OFF)
                for i in range(buffer_size):
                    self.__buffers['real_time_data'][i] = bits_order_reverse_lut[
                        Images.BLUETOOTH_OFF[buffer_size - 1 - i]
                    ]

            self.__epd.display_partial(
                self.__buffers['real_time_data'],
                0, 0,
                self.__epd.width, self.__epd.height - Epaper.__static_area_height
            )

        def __reverse_part_of_buffer(self, buffer_name: str, start: int, end: int):
            """
            Reversing part of buffer.
            :param buffer_name: name of buffer to reverse its part (must have 100% width)
            :param start: vertical start position in pixels from top
            :param end: vertical end position in pixels from top
            """
            start = start * (self.__epd.width // 8)
            end = end * (self.__epd.width // 8)

            size = (end - start) // 2
            for i in range(size):
                swap_index = end - 1 - i
                swap = self.__buffers[buffer_name][start + i]
                self.__buffers[buffer_name][start + i] = bits_order_reverse_lut[
                    self.__buffers[buffer_name][swap_index]
                ]
                self.__buffers[buffer_name][swap_index] = bits_order_reverse_lut[swap]

else:
    class Epaper:
        def __init__(self):
            pass

        def close(self):
            pass

        def restart(self):
            pass

        @property
        def width(self):
            return 128

        @property
        def height(self):
            return 296

        def __prepare(self):
            pass

        def clear(self, init_only=False):
            pass

        def draw_text(self, text: str, y: int):
            pass

        def draw_logo(self):
            pass

        def draw_static_area(self, temperature: float, wind_direction: float, wind_speed: float, city_name: str):
            pass

        def draw_real_time_data(self, speed: float, gps_statistics: dict[str, float], map_preview: bytes,
                                wind_direction: float, bluetooth_connection_status: bool):
            pass
