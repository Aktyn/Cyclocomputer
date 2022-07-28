import _thread
import struct
import time

from src.battery.battery import Battery
from src.bluetooth.bluetooth import Bluetooth
from src.bluetooth.message import Message, STAMP, is_stamp, is_correct_map_preview_data, IMAGE_DATA_PREFIX
from src.common.utils import parse_time
from src.epaper.epaper import Epaper
from src.speedometer import Speedometer
from src.temperature import Temperature


class MODE:
    WELCOME_SCREEN = 0
    DATA_SCREEN = 1
    SLEEP_MODE = 2


class Core:
    def __init__(self):
        self.__running = False
        self.__mode = MODE.WELCOME_SCREEN
        self.__refresh_main_view = False

        self.__previous_realtime_data: dict[str, float] = {
            'speed': 0,
            'altitude': 0,
            'slope': 0,
            'heading': 0,
            'map_preview_changed': False,
            'ride_progress_changed': False,
            'paired': False
        }
        self.__bluetooth_data_buffer = bytes()
        self.__map_preview_data = bytes([0xff] * (128 * 128 // 8))
        self.__gps_statistics = {
            'altitude': 0.,
            'slope': 0.,
            'heading': 0.
        }

        self.__ride_progress = {
            'rideDuration': 0.,
            'timeInMotion': 0.,
            'traveledDistance': 0.,
            'altitudeChange': {
                'up': 0.,
                'down': 0.
            }
        }

        self.__wind_direction = 0
        self.__wind_speed = 0
        self.__city_name = '-'

        self.__temperature = Temperature()
        self.__battery = Battery()
        self.__speedometer = Speedometer(circumference=223)
        self.__epaper = Epaper()
        self.__last_ride_progress_update_time = time.ticks_ms()
        self.__last_epaper_restart_time = time.ticks_ms()
        self.__last_any_activity_time = time.ticks_ms()

        self.__bluetooth = Bluetooth(
            connection_callback=self.__on_bluetooth_connection,
            disconnect_callback=lambda: print("Bluetooth connection lost"),
            data_callback=self.__handle_bluetooth_data
        )

    def close(self):
        self.__running = False
        self.__epaper.close()

    def __time_for_ride_progress_update(self):
        if not self.__bluetooth.paired:
            return False

        if round(self.__speedometer.current_speed) == 0 and round(self.__previous_realtime_data['speed']) > 0:
            return True

        # 1e3 * 60 * 1 = 60000 milliseconds = 1 minute
        return time.ticks_diff(time.ticks_ms(), self.__last_ride_progress_update_time) > 60000

    def __time_for_epaper_restart(self):
        # 1e3 * 60 * 10 = 600000 milliseconds = 10 minutes
        return time.ticks_diff(time.ticks_ms(), self.__last_epaper_restart_time) > 600000

    def __time_for_sleep_mode(self):
        # 1e3 * 60 * 30 = 1800000 milliseconds = 30 minutes
        return time.ticks_diff(time.ticks_ms(), self.__last_any_activity_time) > 1800000

    def __request_ride_progress_update(self):
        self.__last_ride_progress_update_time = time.ticks_ms()
        print("Requesting ride progress update")
        self.__bluetooth.send_message(Message.REQUEST_PROGRESS_DATA)

    def __restart_epaper(self):
        self.__last_epaper_restart_time = time.ticks_ms()
        print("Restarting epaper")
        self.__epaper.restart()

    def __start_sleep_mode(self):
        if self.__mode == MODE.SLEEP_MODE:
            return
        print("Entering sleep mode")
        self.__mode = MODE.SLEEP_MODE
        self.__last_any_activity_time = time.ticks_ms()
        self.__draw_sleep_mode()

    def __draw_sleep_mode(self):
        self.__epaper.clear()
        self.__epaper.draw_logo()
        top = self.__epaper.height // 2 - 64 + 32
        self.__epaper.draw_text('Cyclocomputer\nMade by Aktyn\n\nWaiting for\nphone connection\nor speed results', top)

    def start(self):
        self.__running = True

        self.__epaper.draw_logo()

        top = self.__epaper.height // 2 - 64 + 32
        self.__epaper.draw_text('Cyclocomputer', top)
        time.sleep(0.2)
        self.__epaper.draw_text('Cyclocomputer\nMade by Aktyn', top)
        time.sleep(0.2)
        self.__epaper.draw_text('Cyclocomputer\nMade by Aktyn\n\nWaiting for\nphone connection\nor speed results', top)

        # noinspection PyUnresolvedReferences
        _thread.start_new_thread(self.__second_thread, ())

        ticks_to_next_10sec_update = 0

        while self.__running:
            if self.__refresh_main_view:
                if self.__time_for_epaper_restart():
                    self.__restart_epaper()
                else:
                    self.__epaper.clear(init_only=True)

                self.__draw_main_view()
                self.__redraw_realtime_data(force=True)
                try:
                    time.sleep_ms(1)
                except KeyboardInterrupt:
                    break
                self.__refresh_main_view = False
                continue

            if self.__mode == MODE.DATA_SCREEN:
                ticks_to_next_10sec_update += 1
                if ticks_to_next_10sec_update > 5000:  # roughly every 10 seconds
                    ticks_to_next_10sec_update = 0

                    if self.__time_for_sleep_mode():
                        self.__start_sleep_mode()
                        continue

                    if self.__time_for_epaper_restart():
                        self.__restart_epaper()
                        self.__draw_main_view()
                        self.__redraw_realtime_data(force=True)
                        continue

                    if self.__time_for_ride_progress_update():
                        self.__request_ride_progress_update()
                        continue

                self.__redraw_realtime_data()

                try:
                    time.sleep_ms(1)
                except KeyboardInterrupt:
                    break
                continue

            if self.__speedometer.current_speed >= 0.5:  # Some activity detected
                self.__refresh_main_view = True
                self.__mode = MODE.DATA_SCREEN
                continue

            # Idle mode
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

    def __draw_main_view(self):
        if self.__bluetooth.paired:
            print("Requesting settings data")
            self.__bluetooth.send_message(Message.REQUEST_SETTINGS)

        print(
            f"Battery: {round(self.__battery.level * 100)}%; {'charging' if self.__battery.charging else 'discharging'}")
        self.__epaper.draw_static_area(
            self.__temperature.get_celsius(), self.__wind_direction, self.__wind_speed, self.__city_name,
            self.__battery.level, self.__battery.charging
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

        if round(self.__speedometer.current_speed) == 0 and self.__previous_realtime_data['ride_progress_changed']:
            return True

        if self.__previous_realtime_data['paired'] != self.__bluetooth.paired:
            return True

        return False

    def __redraw_realtime_data(self, force=False):
        if self.__epaper.busy:
            return

        data_changed = self.__realtime_data_changed()

        if not data_changed and not force:
            return

        try:
            # print(f"Sending current speed update ({round(self.__speedometer.current_speed, 2)}km/h)")
            self.__bluetooth.send_message(Message.UPDATE_SPEED, struct.pack('f', self.__speedometer.current_speed))
        except Exception as e:
            print(e)

        self.__last_any_activity_time = time.ticks_ms()

        self.__previous_realtime_data['speed'] = self.__speedometer.current_speed
        self.__previous_realtime_data['altitude'] = self.__gps_statistics['altitude']
        self.__previous_realtime_data['slope'] = self.__gps_statistics['slope']
        self.__previous_realtime_data['heading'] = self.__gps_statistics['heading']
        self.__previous_realtime_data['paired'] = self.__bluetooth.paired
        self.__previous_realtime_data['map_preview_changed'] = False
        self.__previous_realtime_data['ride_progress_changed'] = False
        self.__epaper.draw_real_time_data(
            self.__speedometer.current_speed,
            self.__ride_progress,
            self.__gps_statistics,
            self.__map_preview_data,
            self.__wind_direction,
            self.__bluetooth.paired
        )

    def __on_bluetooth_connection(self):
        print("Bluetooth connection established")
        if self.__mode != MODE.DATA_SCREEN:
            self.__mode = MODE.DATA_SCREEN
            self.__refresh_main_view = True

    def __handle_message(self, message: int, data: bytes):
        self.__last_any_activity_time = time.ticks_ms()

        if message == 1:  # SET_CIRCUMFERENCE
            circumference = struct.unpack('f', data)[0]
            self.__speedometer.set_circumference(circumference)
            print(f"Circumference set to {circumference} cm")
        elif message == 2:  # SET_MAP_PREVIEW
            if is_correct_map_preview_data(data):
                print("Updating map preview image")
                del self.__map_preview_data
                self.__map_preview_data = data[
                                          len(IMAGE_DATA_PREFIX):
                                          len(IMAGE_DATA_PREFIX) + (128 * 128 // 8)
                                          ]
                self.__previous_realtime_data['map_preview_changed'] = True
            else:
                print("Invalid map preview data")
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
        elif message == 5:  # SET_PROGRESS_DATA
            if len(data) >= 20:
                ride_duration = struct.unpack('f', data[:4])[0]
                time_in_motion = struct.unpack('f', data[4:8])[0]
                traveled_distance = struct.unpack('f', data[8:12])[0]
                up = struct.unpack('f', data[12:16])[0]
                down = struct.unpack('f', data[16:20])[0]

                changed = ride_duration != self.__ride_progress['rideDuration'] or \
                          time_in_motion != self.__ride_progress['timeInMotion'] or \
                          round(traveled_distance * 1000) != round(self.__ride_progress['traveledDistance'] * 1000) or \
                          round(up) != round(self.__ride_progress['altitudeChange']['up']) or \
                          round(down) != round(self.__ride_progress['altitudeChange']['down'])

                print(
                    f"Received ride progress data: duration: {parse_time(round(ride_duration))}; time in motion: {parse_time(round(time_in_motion))}; traveled distance: {traveled_distance}km; up: {up}m; down: {down}m; changed: {changed}")

                self.__ride_progress['rideDuration'] = ride_duration
                self.__ride_progress['timeInMotion'] = time_in_motion
                self.__ride_progress['traveledDistance'] = traveled_distance
                self.__ride_progress['altitudeChange']['up'] = up
                self.__ride_progress['altitudeChange']['down'] = down
                self.__previous_realtime_data['ride_progress_changed'] = changed

    def __handle_bluetooth_data(self, data: bytes):
        # print(f"Received {len(data)} bytes")
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
                # print(
                #     f"Awaiting {raw_data_size + metadata_size - len(self.__bluetooth_data_buffer)} more bytes for message {message}")
                return
            raw_data = self.__bluetooth_data_buffer[metadata_size:metadata_size + raw_data_size]
            print(f"Received message: {message}; raw data size: {raw_data_size};")
            try:
                self.__handle_message(message, raw_data)
            except Exception as e:
                print(f"Exception: {e}")
            self.__bluetooth_data_buffer = self.__bluetooth_data_buffer[raw_data_size + metadata_size:]
            if len(self.__bluetooth_data_buffer) >= metadata_size:
                self.__handle_bluetooth_data(bytes())
        except Exception as e:
            print(f"Exception: {e}")

    def __second_thread(self):
        while self.__running:
            self.__speedometer.update()
            self.__bluetooth.update()
            self.__temperature.update()

            try:
                time.sleep_us(1)
            except AttributeError:
                time.sleep(1e-6)
            except KeyboardInterrupt:
                break
        return
