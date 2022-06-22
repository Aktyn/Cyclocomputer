import time

from src.common.utils import mock_speedometer

if not mock_speedometer():
    # noinspection PyPackageRequirements
    from machine import Pin
    import _thread


    class Speedometer:
        __IDLE_DURATION = 8

        def __init__(self, circumference: float):
            """
            :param circumference: The circumference of the wheel in cm.
            """
            self.__circumference = circumference
            self.__running = False
            self.__current_speed = 0
            self.__last_active_timestamp = None
            self.__magnetic_sensor = Pin(0, Pin.IN, Pin.PULL_UP)

        def stop(self):
            self.__running = False

        def start(self):
            if self.__running:
                return

            self.__running = True
            # noinspection PyUnresolvedReferences
            _thread.start_new_thread(self.__start_measuring_speed, ())

        def __start_measuring_speed(self):
            active = False
            while self.__running:
                val = self.__magnetic_sensor.value()
                if val == 0 and not active:
                    active = True
                    self.__on_sensor_active()
                elif val == 1 and active:
                    active = False
                elif self.__last_active_timestamp is not None and \
                        time.ticks_diff(time.ticks_us(), self.__last_active_timestamp) > \
                        Speedometer.__IDLE_DURATION * 1e6:
                    self.__current_speed = 0
                time.sleep_us(1)
            return

        def __on_sensor_active(self):
            timestamp = time.ticks_us()
            time_diff = 0 if self.__last_active_timestamp is None else \
                time.ticks_diff(timestamp, self.__last_active_timestamp)
            if time_diff > 0:
                centimeters_per_nanosecond = self.__circumference / float(time_diff)
                # Multiply by number of microseconds in hour divided by number of centimeters in kilometer
                self.__current_speed = centimeters_per_nanosecond * ((1e6 * 3600) / 100000)
            self.__last_active_timestamp = timestamp

        def get_current_speed(self):
            """
            Returns the current speed in km/h.
            """
            if not self.__running:
                raise Exception("Speedometer is not running")

            return self.__current_speed

else:
    class Speedometer:
        # noinspection PyUnusedLocal
        def __init__(self, circumference: float):
            pass

        def stop(self):
            pass

        def start(self):
            pass

        # noinspection PyMethodMayBeStatic
        def get_current_speed(self):
            return 0
