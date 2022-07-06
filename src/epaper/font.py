import framebuf


class Font:
    class ALIGN:
        LEFT = 0
        CENTER = 1
        RIGHT = 2

    def __init__(self, buffer: bytearray, buffer_width: int, buffer_height: int, glyphs: dict[str, dict[str, int]],
                 size: int):
        self.__frame_buffer = framebuf.FrameBuffer(
            buffer, buffer_width, buffer_height, framebuf.MONO_HLSB
        )
        self.__buffer_width = buffer_width
        self.__buffer_height = buffer_height
        self.__glyphs = glyphs
        self.__size = size

    def __draw_glyph(
            self,
            target: framebuf.FrameBuffer, target_size: tuple[int, int],
            glyph: dict[str, int], start_x: int, start_y: int
    ):
        # Example glyph value: { 'x': 0, 'y': 34, 'width': 25, 'height': 31, 'xoffset': 0, 'yoffset': 10, 'xadvance': 25 }

        for y in range(glyph['height']):
            for x in range(glyph['width']):
                target_x = start_x + (glyph['width'] - 1 - x)
                target_y = start_y - y + self.__size - glyph['yoffset']
                if target_x >= target_size[0] or target_y >= target_size[1]:
                    continue
                pixel = self.__frame_buffer.pixel(
                    x + glyph['x'],
                    y + glyph['y']
                )
                target.pixel(target_x, target_y, pixel)

    def __measure_text(self, text: str):
        width = 0
        for char in text:
            if char in self.__glyphs:
                width += self.__glyphs[char]['xadvance']
        return width

    def draw(self, text: str,
             target: framebuf.FrameBuffer, target_width: int, target_height: int,
             offset_x: int, offset_y: int, align: 'Font.ALIGN' = None
             ):
        text_width = self.__measure_text(text)

        pivot_x = target_width - offset_x
        pivot_y = target_height - offset_y
        if align == Font.ALIGN.RIGHT:
            pivot_x = text_width - offset_x
        elif align == Font.ALIGN.CENTER or align is None:
            pivot_x = (target_width + text_width) // 2 - offset_x

        for char in text:
            if char in self.__glyphs:
                glyph = self.__glyphs[char]
                pivot_x -= glyph['xadvance']
                self.__draw_glyph(target, (target_width, target_height), glyph, pivot_x, pivot_y)
            else:
                print("Unknown character:", char)
