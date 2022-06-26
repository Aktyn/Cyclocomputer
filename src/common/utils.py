import sys


def mock_temperature_sensor():
    return "MOCK_TEMPERATURE_SENSOR" in map(lambda arg: arg.upper(), sys.argv)


def mock_speedometer():
    return "MOCK_SPEEDOMETER" in map(lambda arg: arg.upper(), sys.argv)


def mock_epaper():
    return "MOCK_EPAPER" in map(lambda arg: arg.upper(), sys.argv)


def mock_bluetooth():
    return "MOCK_BLUETOOTH" in map(lambda arg: arg.upper(), sys.argv)
