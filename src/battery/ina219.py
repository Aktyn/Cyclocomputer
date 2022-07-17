# noinspection PyPackageRequirements
from machine import I2C


class BusVoltageRange:
    """Constants for ``bus_voltage_range``"""
    RANGE_16V = 0x00  # set bus voltage range to 16V
    RANGE_32V = 0x01  # set bus voltage range to 32V (default)


class Gain:
    """Constants for ``gain``"""
    DIV_1_40MV = 0x00  # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV = 0x01  # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV = 0x02  # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV = 0x03  # shunt prog. gain set to /8, 320 mV range


class ADCResolution:
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""
    ADCRES_9BIT_1S = 0x00  # 9bit,   1 sample,     84us
    ADCRES_10BIT_1S = 0x01  # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S = 0x02  # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S = 0x03  # 12 bit,  1 sample,    532us
    ADCRES_12BIT_2S = 0x09  # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S = 0x0A  # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S = 0x0B  # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S = 0x0C  # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S = 0x0D  # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S = 0x0E  # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S = 0x0F  # 12bit, 128 samples, 68.10ms


class Mode:
    """Constants for ``mode``"""
    POWERDOW = 0x00  # power down
    SVOLT_TRIGGERED = 0x01  # shunt voltage triggered
    BVOLT_TRIGGERED = 0x02  # bus voltage triggered
    SANDBVOLT_TRIGGERED = 0x03  # shunt and bus voltage triggered
    ADCOFF = 0x04  # ADC off
    SVOLT_CONTINUOUS = 0x05  # shunt voltage continuous
    BVOLT_CONTINUOUS = 0x06  # bus voltage continuous
    SANDBVOLT_CONTINUOUS = 0x07  # shunt and bus voltage continuous


class INA219:
    # Config Register (R/W)
    _REG_CONFIG = 0x00
    # SHUNT VOLTAGE REGISTER (R)
    _REG_SHUNTVOLTAGE = 0x01

    # BUS VOLTAGE REGISTER (R)
    _REG_BUSVOLTAGE = 0x02

    # POWER REGISTER (R)
    _REG_POWER = 0x03

    # CURRENT REGISTER (R)
    _REG_CURRENT = 0x04

    # CALIBRATION REGISTER (R/W)
    _REG_CALIBRATION = 0x05

    def __init__(self, i2c_bus=1, addr=0x40):
        self.i2c = I2C(i2c_bus)
        self.addr = addr

        # Set chip to known config values to start
        self.gain = Gain.DIV_8_320MV
        self._current_lsb = 1
        self._cal_value = 4096
        self._power_lsb = .002

        self.write(INA219._REG_CALIBRATION, self._cal_value)

        self.bus_voltage_range = BusVoltageRange.RANGE_32V

        self.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
        self.mode = Mode.SANDBVOLT_CONTINUOUS
        self.config = self.bus_voltage_range << 13 | self.gain << 11 | self.bus_adc_resolution << 7 | self.shunt_adc_resolution << 3 | self.mode
        self.write(INA219._REG_CONFIG, self.config)

    def read(self, address):
        data = self.i2c.readfrom_mem(self.addr, address, 2)
        return (data[0] * 256) + data[1]

    def write(self, address, data):
        temp = [0, 0]
        temp[1] = data & 0xFF
        temp[0] = (data & 0xFF00) >> 8
        self.i2c.writeto_mem(self.addr, address, bytes(temp))

    def getShuntVoltage_mV(self):
        value = self.read(INA219._REG_SHUNTVOLTAGE)
        if value > 32767:
            value -= 65535
        return value * 0.01

    def getBusVoltage_V(self):
        self.read(INA219._REG_BUSVOLTAGE)  # TODO: check whether this is necessary
        return (self.read(INA219._REG_BUSVOLTAGE) >> 3) * 0.004

    def getCurrent_mA(self):
        value = self.read(INA219._REG_CURRENT)
        if value > 32767:
            value -= 65535
        return value * self._current_lsb

#     ina219 = INA219(addr=0x43)
#     while True:
#         bus_voltage = ina219.getBusVoltage_V()             # voltage on V- (load side)
#         current = ina219.getCurrent_mA()                   # current in mA
#         P = (bus_voltage -3)/1.2*100
#         if(P<0):P=0
#         elif(P>100):P=100
#
#         # INA219 measure bus voltage on the load side. So PSU voltage = bus_voltage + shunt_voltage
#         print("Voltage:  {:6.3f} V".format(bus_voltage))
#         print("Current:  {:6.3f} A".format(current/1000))
#         print("Percent:  {:6.1f} %".format(P))
#         print("")
#
#         time.sleep(2)
