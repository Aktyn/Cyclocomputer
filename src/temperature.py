# noinspection PyPackageRequirements
from machine import ADC
import time

from src.common.utils import linearly_weighted_average


class Temperature:
    CONVERSION_FACTOR = 3.3 / 65535
    HISTORY_SIZE = 8

    def __init__(self):
        self.__sensor = ADC(4)
        self.__next_check_ticks_counter = 0
        self.__last_measurement_timestamp = time.ticks_ms()
        self.__measurements_history: list[float] = []

    def __measure_celsius(self):
        self.__last_measurement_timestamp = time.ticks_ms()
        temperature_sensor_voltage = self.__sensor.read_u16() * Temperature.CONVERSION_FACTOR
        return 27 - (temperature_sensor_voltage - 0.706) / 0.001721

    def get_celsius(self):
        values = self.__measurements_history + [self.__measure_celsius()]
        return linearly_weighted_average(values)

    def update(self):
        self.__next_check_ticks_counter += 1
        if self.__next_check_ticks_counter >= 1000:
            self.__next_check_ticks_counter = 0

            if time.ticks_diff(time.ticks_ms(), self.__last_measurement_timestamp) > 60000:  # 1 minute
                self.__measurements_history.append(self.__measure_celsius())
                if len(self.__measurements_history) > Temperature.HISTORY_SIZE:
                    self.__measurements_history.pop(0)
