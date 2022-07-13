import _thread
import struct
import time

from src.bluetooth.bluetooth import Bluetooth
from src.bluetooth.message import Message, STAMP, is_stamp
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
        self.__refresh_main_view = False

        self.__previous_realtime_data: dict[str, float] = {
            'speed': 0,
            'altitude': 0,
            'slope': 0,
            'heading': 0,
            'map_preview_changed': False
        }
        self.__bluetooth_data_buffer = bytes()
        self.__map_preview_data = bytes()
        self.__gps_statistics = {
            'altitude': 0,
            'slope': 0,
            'heading': 0
        }

        self.__wind_direction = 0
        self.__wind_speed = 0
        self.__city_name = '-'

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

        while self.__running:
            if self.__refresh_main_view:
                self.__epaper.clear(init_only=True)
                self.__draw_main_view()
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    break
                self.__refresh_main_view = False
                continue

            if self.__mode == MODE.DATA_SCREEN:
                self.__redraw_realtime_data()

                try:
                    time.sleep_ms(1)
                except KeyboardInterrupt:
                    break
                continue
            elif self.__speedometer.current_speed > 0:  # Some activity detected
                self.__refresh_main_view = True
                self.__mode = MODE.DATA_SCREEN

            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

    def __draw_main_view(self):
        print("Requesting settings data")
        self.__bluetooth.send_message(Message.REQUEST_SETTINGS)

        self.__epaper.draw_static_area(
            self.__temperature.get_celsius(), self.__wind_direction, self.__wind_speed, self.__city_name
        )

    def __realtime_data_changed(self):
        # NOTE the rounding. It should match rounding parameters during realtime data rendering on epaper

        if round(self.__previous_realtime_data['speed']) != round(self.__speedometer.current_speed):
            return True

        if round(self.__previous_realtime_data['altitude']) != round(self.__gps_statistics['altitude']):
            return True

        if round(self.__previous_realtime_data['slope'], 1) != round(self.__gps_statistics['slope'], 1):
            return True

        if round(self.__previous_realtime_data['heading']) != round(self.__gps_statistics['heading']):
            return True

        if self.__previous_realtime_data['map_preview_changed']:
            return True

        return False

    def __redraw_realtime_data(self, force=False):
        data_changed = self.__realtime_data_changed()

        if not data_changed and not force:
            return

        try:
            print(f"Sending current speed update ({round(self.__speedometer.current_speed, 2)}km/h)")
            self.__bluetooth.send_message(Message.CURRENT_SPEED, struct.pack('f', self.__speedometer.current_speed))
        except Exception as e:
            print(e)

        print("Updating realtime data")
        self.__previous_realtime_data['speed'] = self.__speedometer.current_speed
        self.__previous_realtime_data['altitude'] = self.__gps_statistics['altitude']
        self.__previous_realtime_data['slope'] = self.__gps_statistics['slope']
        self.__previous_realtime_data['heading'] = self.__gps_statistics['heading']
        self.__previous_realtime_data['map_preview_changed'] = False
        self.__epaper.draw_real_time_data(
            self.__speedometer.current_speed,
            self.__gps_statistics,
            self.__map_preview_data,
            self.__wind_direction
        )

    def __on_bluetooth_connection(self):
        print("Bluetooth connection established")
        if self.__mode != MODE.DATA_SCREEN:
            self.__refresh_main_view = True
            self.__mode = MODE.DATA_SCREEN

    def __handle_message(self, message: int, data: bytes):
        if message == 1:  # SET_CIRCUMFERENCE
            circumference = struct.unpack('f', data)[0]
            self.__speedometer.set_circumference(circumference)
            print("Circumference set to:", circumference)
        elif message == 2:  # SET_MAP_PREVIEW
            print("Updating map preview image")
            del self.__map_preview_data
            self.__map_preview_data = data
            self.__previous_realtime_data['map_preview_changed'] = True
        elif message == 3:  # SET GPS STATISTICS
            print("Updating GPS statistics (altitude, slope and heading)")
            self.__gps_statistics['altitude'] = struct.unpack('f', data[:4])[0]
            self.__gps_statistics['slope'] = struct.unpack('f', data[4:8])[0]
            self.__gps_statistics['heading'] = struct.unpack('f', data[8:12])[0]
        elif message == 4:  # SET WEATHER DATA
            self.__wind_direction = struct.unpack('f', data[:4])[0]  # degrees
            self.__wind_speed = struct.unpack('f', data[4:8])[0]  # m/s
            self.__city_name = data[8:].decode('ascii')
            print(
                f"Updating weather data; wind direction: {self.__wind_direction}°; wind speed: {self.__wind_speed}m/s; city: {self.__city_name}")
            if self.__mode == MODE.DATA_SCREEN:
                self.__refresh_main_view = True

    def __handle_bluetooth_data(self, data: bytes):
        print(f"Received {len(data)} bytes")
        self.__bluetooth_data_buffer += data

        metadata_size = 15

        if len(self.__bluetooth_data_buffer) < len(STAMP):
            return

        if not is_stamp(self.__bluetooth_data_buffer[:len(STAMP)]):
            del self.__bluetooth_data_buffer
            self.__bluetooth_data_buffer = bytes()
            return

        if len(self.__bluetooth_data_buffer) < metadata_size:
            return

        try:
            message = self.__bluetooth_data_buffer[len(STAMP)]
            raw_data_size = (self.__bluetooth_data_buffer[len(STAMP) + 1] << 0) + \
                            (self.__bluetooth_data_buffer[len(STAMP) + 2] << 8) + \
                            (self.__bluetooth_data_buffer[len(STAMP) + 3] << 16) + \
                            (self.__bluetooth_data_buffer[len(STAMP) + 4] << 24)
            if len(self.__bluetooth_data_buffer) < raw_data_size + metadata_size:
                print(
                    f"Awaiting {raw_data_size + metadata_size - len(self.__bluetooth_data_buffer)} more bytes for message {message}")
                return
            raw_data = self.__bluetooth_data_buffer[metadata_size:metadata_size + raw_data_size]
            print(f"Received message: {message}; raw data size: {raw_data_size};")
            try:
                self.__handle_message(message, raw_data)
            except Exception as e:
                print(e)
            self.__bluetooth_data_buffer = self.__bluetooth_data_buffer[raw_data_size + metadata_size:]
            if len(self.__bluetooth_data_buffer) >= metadata_size:
                self.__handle_bluetooth_data(bytes())
        except Exception as e:
            print(f"Exception: {e}")

    def __second_thread(self):
        while self.__running:
            self.__speedometer.update()
            self.__bluetooth.update()

            try:
                time.sleep_us(1)
            except AttributeError:
                time.sleep(1e-6)
            except KeyboardInterrupt:
                break
        return
