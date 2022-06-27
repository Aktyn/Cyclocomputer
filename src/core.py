import _thread
import time

import sys

from src.bluetooth.bluetooth import Bluetooth
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

        self.__temperature = Temperature()
        self.__speedometer = Speedometer(circumference=223)
        self.__epaper = Epaper()

        self.__bluetooth = Bluetooth(
            connection_callback=self.__on_bluetooth_connection,
            disconnect_callback=lambda: print("Bluetooth connection lost"),
            data_callback=lambda data: print("Received data:", data)
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

            print(
                f"Temperature: {self.__temperature.get_celsius()}°C; Speed: {self.__speedometer.current_speed}km/h"
            )
            # if refreshed:
            #     self.__epaper.draw_line(
            #         f"Temp: {round(self.__temperature.get_celsius(), 2)}C\nSpeed: {round(current_speed, 2)}km/h",
            #         top
            #     )
            # elif current_speed > 0:
            #     refreshed = True
            #     self.__epaper.clear(init_only=True)
            #     self.__epaper.draw_logo()

            if self.__mode == MODE.DATA_SCREEN:
                self.__redraw_realtime_data()
            elif self.__speedometer.current_speed > 0:  # Some activity detected
                self.__epaper.clear(init_only=True)
                self.__draw_main_view()
            # else:
            #     # TODO: remove after testing
            #     self.__epaper.clear(init_only=True)
            #     self.__draw_main_view()
            #     for s in range(7, 13):
            #         self.__epaper.draw_speed(s, refresh_only_speed_area=True)
            #         time.sleep_ms(16)
            #     sys.exit(0)

            try:
                if self.__speedometer.current_speed == 0:
                    time.sleep(1)
                else:
                    time.sleep_ms(1)
            except KeyboardInterrupt:
                break

    def __draw_main_view(self):
        # TODO: refresh it periodically but not too often
        self.__epaper.draw_static_area(self.__temperature.get_celsius())

        self.__mode = MODE.DATA_SCREEN

    def __redraw_realtime_data(self):
        # TODO: do not redraw if nothing changed
        self.__epaper.draw_speed(self.__speedometer.current_speed)

    def __on_bluetooth_connection(self):
        print("Bluetooth connection established")
        if self.__mode != MODE.DATA_SCREEN:
            self.__epaper.clear(init_only=True)
            self.__draw_main_view()

    def __second_thread(self):
        while self.__running:
            self.__speedometer.update()
            self.__bluetooth.update()

            try:
                time.sleep_us(1)
            except KeyboardInterrupt:
                break
        return
