# noinspection PyPackageRequirements
from machine import ADC


class Temperature:
    CONVERSION_FACTOR = 3.3 / 65535

    def __init__(self):
        self.__sensor = ADC(4)

    def get_celsius(self):
        temperature_sensor_voltage = self.__sensor.read_u16() * Temperature.CONVERSION_FACTOR
        return 27 - (temperature_sensor_voltage - 0.706) / 0.001721
