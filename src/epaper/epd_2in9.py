# noinspection PyPackageRequirements
from machine import Pin, SPI
# noinspection PyPackageRequirements
import utime

# Display resolution
EPD_WIDTH = 128
EPD_HEIGHT = 296


# noinspection PyPep8Naming
class EPD_2in9:
    RST_PIN = 12
    DC_PIN = 8
    CS_PIN = 9
    BUSY_PIN = 13

    WF_PARTIAL_2IN9 = [
        0x0, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x80, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x40, 0x40, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x80, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0A, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1,
        0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0,
        0x22, 0x22, 0x22, 0x22, 0x22, 0x22, 0x0, 0x0, 0x0,
        0x22, 0x17, 0x41, 0xB0, 0x32, 0x36,
    ]

    def __init__(self):
        self.reset_pin = Pin(EPD_2in9.RST_PIN, Pin.OUT)

        self.busy_pin = Pin(EPD_2in9.BUSY_PIN, Pin.IN, Pin.PULL_UP)
        self.cs_pin = Pin(EPD_2in9.CS_PIN, Pin.OUT)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.lut = EPD_2in9.WF_PARTIAL_2IN9

        self.spi = SPI(1)
        self.spi.init(baudrate=4000_000)
        self.dc_pin = Pin(EPD_2in9.DC_PIN, Pin.OUT)

        self.init()

    @staticmethod
    def __digital_write(pin: Pin, value: float):
        pin.value(value)

    @staticmethod
    def __digital_read(pin: Pin):
        return pin.value()

    @staticmethod
    def __delay_ms(milliseconds: int):
        utime.sleep(milliseconds / 1000.0)

    def spi_write_byte(self, data):
        self.spi.write(bytearray(data))

    def module_exit(self):
        self.__digital_write(self.reset_pin, 0)

    # Hardware reset
    def reset(self):
        self.__digital_write(self.reset_pin, 1)
        self.__delay_ms(50)
        self.__digital_write(self.reset_pin, 0)
        self.__delay_ms(2)
        self.__digital_write(self.reset_pin, 1)
        self.__delay_ms(50)

    def send_command(self, command: int):
        self.__digital_write(self.dc_pin, 0)
        self.__digital_write(self.cs_pin, 0)
        self.spi_write_byte([command])
        self.__digital_write(self.cs_pin, 1)

    def send_data(self, data: int):
        self.__digital_write(self.dc_pin, 1)
        self.__digital_write(self.cs_pin, 0)
        self.spi_write_byte([data])
        self.__digital_write(self.cs_pin, 1)

    def read_busy(self):
        # print("e-Paper busy")
        while self.__digital_read(self.busy_pin) == 1:  # 0: idle, 1: busy
            self.__delay_ms(10)
        # print("e-Paper busy release")

    def turn_on_display(self):
        self.send_command(0x22)  # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0xF7)
        self.send_command(0x20)  # MASTER_ACTIVATION
        self.read_busy()

    def turn_on_partial_display(self):
        self.send_command(0x22)  # DISPLAY_UPDATE_CONTROL_2
        self.send_data(0x0F)
        self.send_command(0x20)  # MASTER_ACTIVATION
        self.read_busy()

    def send_lut(self):
        self.send_command(0x32)
        for i in range(0, 153):
            self.send_data(self.lut[i])
        self.read_busy()

    def set_window(self, x_start: int, y_start: int, x_end: int, y_end: int):
        self.send_command(0x44)  # SET_RAM_X_ADDRESS_START_END_POSITION
        # x point must be the multiple of 8 or the last 3 bits will be ignored
        self.send_data((x_start >> 3) & 0xFF)
        self.send_data((x_end >> 3) & 0xFF)
        self.send_command(0x45)  # SET_RAM_Y_ADDRESS_START_END_POSITION
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end >> 8) & 0xFF)

    def set_cursor(self, x: int, y: int):
        self.send_command(0x4E)  # SET_RAM_X_ADDRESS_COUNTER
        self.send_data(x & 0xFF)

        self.send_command(0x4F)  # SET_RAM_Y_ADDRESS_COUNTER
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)
        self.read_busy()

    def init(self):
        # EPD hardware init start
        self.reset()

        self.read_busy()
        self.send_command(0x12)  # SWRESET
        self.read_busy()

        self.send_command(0x01)  # Driver output control
        self.send_data(0x27)
        self.send_data(0x01)
        self.send_data(0x00)

        self.send_command(0x11)  # data entry mode
        self.send_data(0x03)

        self.set_window(0, 0, self.width - 1, self.height - 1)

        self.send_command(0x21)  # Display update control
        self.send_data(0x00)
        self.send_data(0x80)

        self.set_cursor(0, 0)
        self.read_busy()
        # EPD hardware init end
        return 0

    def display(self, image: bytearray):
        if image is None:
            return
        self.send_command(0x24)  # WRITE_RAM
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(image[i + j * int(self.width / 8)])
        self.turn_on_display()

    def display_base(self, image: bytearray):
        if image is None:
            return
        self.send_command(0x24)  # WRITE_RAM
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(image[i + j * int(self.width / 8)])

        self.send_command(0x26)  # WRITE_RAM
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(image[i + j * int(self.width / 8)])

        self.turn_on_display()

    def display_partial(self, image: bytearray, x=0, y=0, width=EPD_WIDTH, height=EPD_HEIGHT):
        """
        :param image: bytebuffer to display
        :param x: horizontal starting position for drawing (works only for 1 pixel height)
        :param y: vertical starting position for drawing
        :param width: should equal to image width (IT MUST BE A MULTIPLE OF 8)
        :param height: should equal to image height
        :return:
        """
        if image is None:
            return

        self.__digital_write(self.reset_pin, 0)
        self.__delay_ms(2)
        self.__digital_write(self.reset_pin, 1)
        self.__delay_ms(2)

        self.send_lut()
        self.send_command(0x37)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x40)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x3C)  # BorderWavefrom
        self.send_data(0x80)

        self.send_command(0x22)
        self.send_data(0xC0)
        self.send_command(0x20)
        self.read_busy()

        self.set_window(x, y, width - 1, height - 1)
        self.set_cursor(x, y)

        self.send_command(0x24)  # WRITE_RAM
        for j in range(height):
            for i in range(int(width / 8)):
                self.send_data(image[i + j * int(width / 8)])
        self.turn_on_partial_display()

    def clear(self, color: int):
        self.send_command(0x24)  # WRITE_RAM
        for j in range(self.height):
            for i in range(int(self.width / 8)):
                self.send_data(color)
        self.turn_on_display()

    def sleep(self):
        self.send_command(0x10)  # DEEP_SLEEP_MODE
        self.send_data(0x01)

        self.__delay_ms(2000)
        self.module_exit()
