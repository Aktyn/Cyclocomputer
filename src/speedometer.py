import time

# noinspection PyPackageRequirements
from machine import Pin


class Speedometer:
    __IDLE_DURATION = 8

    def __init__(self, circumference: float):
        """
        :param circumference: The circumference of the wheel in cm.
        """
        self.__circumference = circumference
        self.__active = False
        self.__current_speed = 0.0
        self.__last_active_timestamp = None
        self.__magnetic_sensor = Pin(2, Pin.IN, Pin.PULL_UP)

    def update(self):
        val = self.__magnetic_sensor.value()
        if val == 0 and not self.__active:
            self.__active = True
            self.__on_sensor_active()
        elif val == 1 and self.__active:
            self.__active = False
        elif self.__last_active_timestamp is not None and \
                time.ticks_diff(time.ticks_us(), self.__last_active_timestamp) > \
                Speedometer.__IDLE_DURATION * 1e6:
            self.__current_speed = 0

    def __on_sensor_active(self):
        timestamp = time.ticks_us()
        time_diff = 0 if self.__last_active_timestamp is None else \
            time.ticks_diff(timestamp, self.__last_active_timestamp)
        if time_diff > 0:
            centimeters_per_nanosecond = self.__circumference / float(time_diff)
            # Multiply by number of microseconds in hour divided by number of centimeters in kilometer
            self.__current_speed = centimeters_per_nanosecond * ((1e6 * 3600) / 100000)
        self.__last_active_timestamp = timestamp

    @property
    def current_speed(self):
        """
        Returns the current speed in km/h.
        """
        return self.__current_speed

    def set_circumference(self, circumference: float):
        self.__circumference = circumference
