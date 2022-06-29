import _thread
import struct
import time

from src.bluetooth.bluetooth import Bluetooth
from src.bluetooth.message import Message
from src.epaper.epaper import Epaper
from src.speedometer import Speedometer
from src.temperature import Temperature


class MODE:
    WELCOME_SCREEN = 0
    DATA_SCREEN = 1


class Core:
    def __init__(self):
        self.__running = False
        # TODO: sleeping mode activating after some time without detected activity with logo and some info view
        self.__mode = MODE.WELCOME_SCREEN

        self.__previous_realtime_data: dict[str, float] = {
            'speed': 0
        }

        self.__temperature = Temperature()
        self.__speedometer = Speedometer(circumference=223)
        self.__epaper = Epaper()

        self.__bluetooth = Bluetooth(
            connection_callback=self.__on_bluetooth_connection,
            # TODO: draw bluetooth disabled icon in place of map until connection will be resored
            disconnect_callback=lambda: print("Bluetooth connection lost"),
            data_callback=self.__handle_bluetooth_data
        )

    def close(self):
        self.__running = False
        self.__epaper.close()

    def start(self):
        self.__running = True

        self.__epaper.draw_logo()

        top = self.__epaper.height // 2 - 64 + 32
        self.__epaper.draw_text('Cyclocomputer', top)
        self.__epaper.draw_text('Cyclocomputer\nMade by Aktyn', top)
        self.__epaper.draw_text('Cyclocomputer\nMade by Aktyn\n\nWaiting for\nphone connection\nor speed results', top)

        # noinspection PyUnresolvedReferences
        _thread.start_new_thread(self.__second_thread, ())

        # refreshed = False
        while self.__running:
            # print(
            #     f"Temperature: {self.__temperature.get_celsius()}°C; Speed: {self.__speedometer.current_speed}km/h"
            # )

            if self.__mode == MODE.DATA_SCREEN:
                self.__redraw_realtime_data()

                try:
                    time.sleep_ms(1)
                except KeyboardInterrupt:
                    break
                continue
            elif self.__speedometer.current_speed > 0:  # Some activity detected
                self.__epaper.clear(init_only=True)
                self.__draw_main_view()

            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

    def __draw_main_view(self):
        # TODO: refresh it periodically but not too often
        print("Requesting settings data")
        self.__bluetooth.send_data(Message.REQUEST_SETTINGS)

        self.__epaper.draw_static_area(self.__temperature.get_celsius())

        self.__mode = MODE.DATA_SCREEN

    def __realtime_data_changed(self):
        if self.__previous_realtime_data['speed'] != self.__speedometer.current_speed:
            return True

        return False

    def __redraw_realtime_data(self):
        data_changed = self.__realtime_data_changed()

        if not data_changed:
            return

        print("Sending current speed update")
        data = bytes(Message.CURRENT_SPEED, 'ascii')
        data += struct.pack('f', self.__speedometer.current_speed)
        self.__bluetooth.send_data(data)
        # self.__bluetooth.send_data(Message.CURRENT_SPEED)

        self.__previous_realtime_data = {
            'speed': self.__speedometer.current_speed,
        }
        self.__epaper.draw_speed(self.__speedometer.current_speed)

    def __on_bluetooth_connection(self):
        print("Bluetooth connection established")
        if self.__mode != MODE.DATA_SCREEN:
            self.__epaper.clear(init_only=True)
            self.__draw_main_view()

    def __handle_bluetooth_data(self, data: bytes):
        # print(f"Received data: {data}")

        # TODO: buffering large data chunks (when raw_data_size exceeds given data bytes)

        try:
            message = data[0]
            raw_data_size = (data[1] << 0) + (data[2] << 8) + (data[3] << 16) + (data[4] << 24)
            raw_data = data[5:5 + raw_data_size]
            print(f"Received message: {message}; raw data size: {raw_data_size}; raw data: {raw_data}")
            if message == 1:  # SET_CIRCUMFERENCE
                circumference = struct.unpack('f', raw_data)[0]
                self.__speedometer.set_circumference(circumference)
                print("Circumference set to:", circumference)
        except Exception as e:
            print(f"Exception: {e}")

    def __second_thread(self):
        while self.__running:
            self.__speedometer.update()
            self.__bluetooth.update()

            try:
                time.sleep_us(1)
            except KeyboardInterrupt:
                break
        return
