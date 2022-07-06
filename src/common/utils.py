import sys


def mock_temperature_sensor():
    return "MOCK_TEMPERATURE_SENSOR" in map(lambda arg: arg.upper(), sys.argv)


def mock_speedometer():
    return "MOCK_SPEEDOMETER" in map(lambda arg: arg.upper(), sys.argv)


def mock_epaper():
    return "MOCK_EPAPER" in map(lambda arg: arg.upper(), sys.argv)


def mock_bluetooth():
    return "MOCK_BLUETOOTH" in map(lambda arg: arg.upper(), sys.argv)


__directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N']


def degrees_to_compass_direction(degrees: float):
    if degrees < 0:
        degrees += 360
    if degrees < 0:
        return '-'
    index = (degrees % 360) / 22.5
    return __directions[round(index)]
