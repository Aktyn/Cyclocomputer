from src.battery.ina219 import INA219


class Battery:
    def __init__(self):
        self.__ina219 = INA219(addr=0x43)

    @property
    def charging(self):
        # self.__ina219.getCurrent_mA() / 1000 -> current in ampere
        return self.__ina219.getCurrent_mA() > 0

    @property
    def level(self):
        bus_voltage = self.__ina219.getBusVoltage_V()  # voltage on V- (load side)
        voltage_factor = (bus_voltage - 3) / 1.2
        if voltage_factor < 0:
            voltage_factor = 0.0
        elif voltage_factor > 1:
            voltage_factor = 1.0
        return voltage_factor
