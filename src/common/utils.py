__directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N']


def degrees_to_compass_direction(degrees: float):
    if degrees < 0:
        degrees += 360
    if degrees < 0:
        return '-'
    index = (degrees % 360) / 22.5
    return __directions[round(index)]
