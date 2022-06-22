import time

import sys

from src.speedometer import Speedometer
from src.temperature import Temperature

temperature = Temperature()
speedometer = Speedometer(circumference=223)

speedometer.start()

while True:
    # TODO: linearly weighted average of last few temperature measurements
    print(f"Temperature: {temperature.get_celsius()}°C; Speed: {speedometer.get_current_speed()}km/h")
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        break

speedometer.stop()
print("Exiting")

sys.exit(0)
