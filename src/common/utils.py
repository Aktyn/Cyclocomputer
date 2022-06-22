import sys


# def cache(fun):
#     cache.response_ = {}
#
#     def inner():
#         if fun.__name__ not in cache.response_:
#             cache.response_[fun.__name__] = fun()
#         return cache.response_[fun.__name__]
#
#     return inner


# @cache
def mock_temperature_sensor():
    return "MOCK_TEMPERATURE_SENSOR" in map(lambda arg: arg.upper(), sys.argv)


# @cache
def mock_speedometer():
    return "MOCK_SPEEDOMETER" in map(lambda arg: arg.upper(), sys.argv)
