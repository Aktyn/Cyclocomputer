from bmp_reader import BMPReader


def rgb2d_to_mono_hlsb(rgb_array: list[list[list[int]]], width: int, height: int):
    mono_hlsb = bytearray(width * height // 8)

    for y in range(height):
        for x in range(width):
            color = round(rgb_array[y][x][0] / 255.0)  # 1 for white and 0 for black
            index = x + y * width
            mono_hlsb[index // 8] |= color << (7 - index % 8)

    return mono_hlsb


if __name__ == '__main__':
    img = BMPReader('./logo.bmp')
    print(rgb2d_to_mono_hlsb(img.get_pixels(), img.width, img.height))
