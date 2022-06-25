import time
import sys

from src.epaper.epaper import Epaper
from src.speedometer import Speedometer
from src.temperature import Temperature

if __name__ == '__main__':
    epaper = Epaper()
    epaper.draw_logo()
    time.sleep(1)

    top = epaper.height // 2 - 64 + 16
    epaper.draw_line('Cyclocomputer', top)
    epaper.draw_line('Cyclocomputer\nMade by Aktyn', top)
    epaper.draw_line('Cyclocomputer\nMade by Aktyn\n\nWaiting for\nphone connection', top)
    time.sleep(1)

    temperature = Temperature()
    speedometer = Speedometer(circumference=223)

    speedometer.start()

    refreshed = False
    while True:
        # TODO: linearly weighted average of last few temperature measurements
        print(f"Temperature: {temperature.get_celsius()}°C; Speed: {speedometer.get_current_speed()}km/h")
        current_speed = speedometer.get_current_speed()
        if refreshed:
            epaper.draw_line(
                f"Temp: {round(temperature.get_celsius(), 2)}C\nSpeed: {round(current_speed, 2)}km/h",
                top
            )
        elif current_speed > 0:
            refreshed = True
            epaper.clear()
            epaper.draw_logo()
            time.sleep(1)

        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    speedometer.stop()
    print("Exiting")

    epaper.close()

    sys.exit(0)
