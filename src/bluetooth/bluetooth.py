import time

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
                self.__pico_ble.uart.write("Remove the interference")
                # time.sleep_ms(20)  # TODO
                data_rx = self.__pico_ble.uart.read(6)
                if data_rx == b"ER+7\r\n":
                    print("Enable notify on the mobile phone\r\n")
                    self.__delay_next_update(1000)
                else:
                    # print("The connection is successful")
                    self.__pico_ble.uart.write("The connection is successful")
                    # time.sleep_ms(100)  # TODO
                    self.__paired = True
                    self.__query_info()
                    self.__connection_callback()

                return

            # Receiving data
            if self.__pico_ble.uart.any() > 0:
                data = self.__pico_ble.uart.read()
                # time.sleep_ms(20)  # TODO
                # print(rx_data)
                self.__data_callback(data)
                self.__pico_ble.uart.write(data)

        def __query_info(self):
            pass
            # TODO
            # # Querying Basic Information
            # Cmd_Process(Baud_Rate_Query)
            # time.sleep_ms(100)
            # Cmd_Process(Low_Power_Query)
            # time.sleep_ms(100)
            # Cmd_Process(Name_BLE_Query)
            # time.sleep_ms(100)
            # Cmd_Process(Name_SPP_Query)
            # time.sleep_ms(100)
            # Cmd_Process(ADD_Query)
            # time.sleep_ms(100)
            # Cmd_Process(BLE_Switch_Query)
            # time.sleep_ms(100)
            # Cmd_Process(SPP_Switch_Query)
            # time.sleep_ms(100)
            #
            # # Change the name of Bluetooth
            # if Cmd_Process(Name_BLE_Set):
            #     print("BLE was successfully renamed to : BLE-Waveshare")
            #     uart.write("BLE was successfully renamed to : BLE-Waveshare")
            # time.sleep_ms(100)
            # if Cmd_Process(Name_SPP_Set):
            #     print("SPP was successfully renamed to : SPP-Waveshare")
            #     uart.write("SPP was successfully renamed to : SPP-Waveshare")
            # time.sleep_ms(100)

        # def __start_thread(self):
        #     self.__running = True
        #     while self.__running:
        #         Pico_BLE_init()
        #         self.__connection_callback()
        #         while self.__running:
        #             if uart.any() > 0:
        #                 rx_data = uart.read()
        #                 time.sleep_ms(20)
        #                 # print(rx_data)
        #                 self.__data_callback(rx_data)
        #                 uart.write(rx_data)
        #         print("Test xyz")
        #     return
else:
    class Bluetooth:
        def __init__(self):
            pass

        def update(self):
            pass
