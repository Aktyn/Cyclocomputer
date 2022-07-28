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


__time_units = [
    {
        'name': 'd',
        'scale': 1000 * 60 * 60 * 24,
    },
    {
        'name': 'h',
        'scale': 1000 * 60 * 60,
    },
    {
        'name': 'min',
        'scale': 1000 * 60,
    },
    {
        'name': 'sec',
        'scale': 1000,
    },
    {
        'name': 'ms',
        'scale': 1,
    },
]


def parse_time(milliseconds: int, round_to='min'):
    if round_to not in ['ms', 'sec', 'min', 'h', 'd']:
        raise ValueError(f"Invalid roundTo value: {round_to}")

    round_index = __time_units.index(next(x for x in __time_units if x['name'] == round_to))
    if milliseconds == 0 or milliseconds < __time_units[round_index]['scale']:
        return f'0 {round_to}'

    milliseconds = round(milliseconds)

    unit_strings: list[str] = []
    for index, unit in enumerate(__time_units):
        if index <= round_index and milliseconds >= unit['scale']:
            unit_value = milliseconds // unit['scale']
            if unit_value > 0:
                milliseconds -= unit_value * unit['scale']
                unit_strings.append(f'{unit_value} {unit["name"]}')

    return ' '.join(unit_strings)
