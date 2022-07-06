from bmp_reader import BMPReader


def rgb2d_to_mono_hlsb(rgb_array: list[list[list[int]]], width: int, height: int):
    # Make sure width * height is a multiple of 8
    padding = 0
    if (width * height) % 8 > 0:
        padding = 8 - ((width * height) % 8)
    mono_hlsb = bytearray((width * height + padding) // 8)

    for y in range(height):
        for x in range(width):
            color = round(rgb_array[x][y][0] / 255.0)  # 1 for white and 0 for black
            # index = x + y * width
            index = y + x * height
            mono_hlsb[index // 8] |= color << (7 - index % 8)

    return mono_hlsb


if __name__ == '__main__':
    for src in ['./logo.bmp', './temperature_40px.bmp', './digits_104px.bmp', './common_24px.bmp']:
        img = BMPReader(src)
        print(f"Source: {src}; width: {img.width}; height: {img.height}")
        print(rgb2d_to_mono_hlsb(img.get_pixels(), img.width, img.height))
        print("")
