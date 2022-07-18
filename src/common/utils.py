__directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N']


def degrees_to_compass_direction(degrees: float):
    if degrees < 0:
        degrees += 360
    if degrees < 0:
        return '-'
    index = (degrees % 360) / 22.5
    return __directions[round(index)]


def linearly_weighted_average(values: list[float], reverse=False):
    sum_ = 0.
    values_count = len(values)
    if values_count == 0:
        return 0.
    # sum of sequence of consecutive integer numbers in range [1, values_count]
    weights_sum = (values_count ** 2 + values_count) / 2

    for index, value in enumerate(values):
        sum_ += value * (index + 1 if not reverse else values_count - index)

    return sum_ / weights_sum
