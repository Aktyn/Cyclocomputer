import struct
import time

from src.bluetooth.base64 import b64encode
from src.bluetooth.message import STAMP
from src.common.utils import mock_bluetooth

if not mock_bluetooth():
    from src.bluetooth.pico_ble import PicoBLE


    class Bluetooth:
        def __init__(self, connection_callback: callable, disconnect_callback: callable, data_callback: callable):
            self.__connected = False
            self.__paired = False
            self.__next_update_time = None
            self.__connection_callback = connection_callback
            self.__disconnect_callback = disconnect_callback
            self.__data_callback = data_callback

            self.__pico_ble = PicoBLE()

        @property
        def paired(self):
            return self.__paired

        def __delay_next_update(self, milliseconds: int):
            self.__next_update_time = time.ticks_add(time.ticks_ms(), milliseconds)

        def update(self):
            if self.__next_update_time is not None:
                now = time.ticks_ms()
                if time.ticks_diff(self.__next_update_time, now) > 0:
                    return
                else:
                    self.__next_update_time = None

            if not self.__connected:
                if self.__pico_ble.ble_mode_pin.value() != 0:
                    self.__connected = True
                else:
                    return
            else:
                if self.__pico_ble.ble_mode_pin.value() == 0:
                    self.__connected = False
                    self.__paired = False
                    self.__disconnect_callback()
                    return

            if not self.__paired:
                print("Pairing...")
                data_rx = self.__pico_ble.uart.read(6)
                if data_rx == b"ER+7\r\n":
                    print("Enable notify on the mobile phone\r\n")
                    self.__delay_next_update(1000)
                else:
                    self.__paired = True
                    self.__pico_ble.query_basic_info()
                    self.__connection_callback()

                return

            # Receiving data
            if self.__pico_ble.uart.any() > 0:
                data = self.__pico_ble.uart.read()
                # print(rx_data)
                self.__data_callback(data)
                # self.__pico_ble.uart.write(data)  # ??

        def send_message(self, message: int, data=bytes()):
            if not self.__paired:
                return

            buffer = STAMP + struct.pack('B', message) + struct.pack('I', len(data)) + data
            base64 = b64encode(buffer)

            print(f"Sending {len(buffer)} bytes; base64: {base64}")
            self.__pico_ble.uart.write(base64)

else:
    class Bluetooth:
        # noinspection PyUnusedLocal
        def __init__(self, connection_callback: callable, disconnect_callback: callable, data_callback: callable):
            pass

        @property
        def paired(self):
            return False

        def update(self):
            pass

        def send_message(self, message: int, data: bytes):
            pass
