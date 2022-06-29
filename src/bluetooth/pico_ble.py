import time
# noinspection PyPackageRequirements
from machine import UART, Pin

# Power-on return message
Power_On_Return_Message_OFF = b"AT+CR00\r\n"
Power_On_Return_Message_ON = b"AT+CR01\r\n"

#  Restore Factory Defaults
Factory_Reset = b"AT+CW\r\n"

# Reset
Reset = b"AT+CZ\r\n"

# Set baud rate
Baud_Rate_9600 = b"AT+CT01\r\n"
Baud_Rate_19200 = b"AT+CT02\r\n"
Baud_Rate_38400 = b"AT+CT03\r\n"
Baud_Rate_57600 = b"AT+CT04\r\n"
Baud_Rate_115200 = b"AT+CT05\r\n"
Baud_Rate_256000 = b"AT+CT06\r\n"
Baud_Rate_512000 = b"AT+CT07\r\n"
Baud_Rate_230400 = b"AT+CT08\r\n"
Baud_Rate_460800 = b"AT+CT09\r\n"
Baud_Rate_1000000 = b"AT+CT10\r\n"
Baud_Rate_31250 = b"AT+CT11\r\n"
Baud_Rate_2400 = b"AT+CT12\r\n"
Baud_Rate_4800 = b"AT+CT13\r\n"
# Query baud rate
Baud_Rate_Query = b"AT+QT\r\n"

# Chip low power Settings
Not_Low_Power = b"AT+CL00\r\n"
Low_Power = b"AT+CL01\r\n"
# Chip low power Query
Low_Power_Query = b"AT+QL\r\n"

# Set the bluetooth name and address
Name_BLE_Set = b"AT+BMBLE-Cyclocomputer\r\n"
Name_SPP_Set = b"AT+BDCyclocomputer\r\n"
ADD_SET = b"AT+BN112233445566\r\n"
# Example Query the name and address of bluetooth
Name_BLE_Query = b"AT+TM\r\n"
Name_SPP_Query = b"AT+TD\r\n"
ADD_Query = b"AT+TN\r\n"

# ON or OFF BLE
BLE_ON = b"AT+B401\r\n"
BLE_OFF = b"AT+B400\r\n"
# BLE Switch Query
BLE_Switch_Query = b"AT+T4\r\n"

# ON or OFF SPP
SPP_ON = b"AT+B501\r\n"
SPP_OFF = b"AT+B500\r\n"
# SPP Switch Query
SPP_Switch_Query = b"AT+T5\r\n"

# ERROR
ERROR_1 = b"ER+1\r\n"
ERROR_2 = b"ER+2\r\n"
ERROR_3 = b"ER+3\r\n"
ERROR_4 = b"ER+4\r\n"
ERROR_5 = b"ER+5\r\n"
ERROR_6 = b"ER+6\r\n"
ERROR_7 = b"ER+7\r\n"
ERROR_8 = b"ER+8\r\n"


# uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
# uart = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))


# txData = b'RS232 receive test...\r\n'
# uart.write(txData)
# time.sleep(0.1)


class PicoBLE:
    def __init__(self):
        self.ble_mode_pin = Pin(15, Pin.IN, Pin.PULL_UP)
        self.uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

    def query_basic_info(self):
        self.__cmd_process(Baud_Rate_Query)
        time.sleep_ms(100)
        self.__cmd_process(Low_Power_Query)
        time.sleep_ms(100)
        self.__cmd_process(Name_BLE_Query)
        time.sleep_ms(100)
        self.__cmd_process(Name_SPP_Query)
        time.sleep_ms(100)
        self.__cmd_process(ADD_Query)
        time.sleep_ms(100)
        self.__cmd_process(BLE_Switch_Query)
        time.sleep_ms(100)
        self.__cmd_process(SPP_Switch_Query)
        time.sleep_ms(100)

        # Change the name of Bluetooth
        if self.__cmd_process(Name_BLE_Set):
            print("BLE was successfully renamed to : BLE-Waveshare")
            self.uart.write("BLE was successfully renamed to : BLE-Waveshare")
        time.sleep_ms(100)
        if self.__cmd_process(Name_SPP_Set):
            print("SPP was successfully renamed to : Cyclocomputer")
            self.uart.write("SPP was successfully renamed to : Waveshare")
        time.sleep_ms(100)

    def __cmd_process(self, data: bytes):
        self.uart.write(data)
        time.sleep_ms(20)
        data_rx = self.uart.read()
        if data_rx is None:
            return False
        if data == Baud_Rate_Query:
            if data_rx[0:3] == b'QT+':
                i = (data_rx[3] - 48) * 10 + data_rx[4] - 48
                if i == 1:
                    print("Bluetooth baud rate is 9600")
                    self.uart.write("Bluetooth baud rate is 9600")
                elif i == 2:
                    print("Bluetooth baud rate is 19200")
                    self.uart.write("Bluetooth baud rate is 19200")
                elif i == 3:
                    print("Bluetooth baud rate is 38400")
                    self.uart.write("Bluetooth baud rate is 38400")
                elif i == 4:
                    print("Bluetooth baud rate is 57600")
                    self.uart.write("Bluetooth baud rate is 57600")
                elif i == 5:
                    print("Bluetooth baud rate is 115200")
                    self.uart.write("Bluetooth baud rate is 115200")
                elif i == 6:
                    print("Bluetooth baud rate is 256000")
                    self.uart.write("Bluetooth baud rate is 256000")
                elif i == 7:
                    print("Bluetooth baud rate is 512000")
                    self.uart.write("Bluetooth baud rate is 512000")
                elif i == 8:
                    print("Bluetooth baud rate is 230400")
                    self.uart.write("Bluetooth baud rate is 230400")
                elif i == 9:
                    print("Bluetooth baud rate is 460800")
                    self.uart.write("Bluetooth baud rate is 460800")
                elif i == 10:
                    print("Bluetooth baud rate is 1000000")
                    self.uart.write("Bluetooth baud rate is 1000000")
                elif i == 11:
                    print("Bluetooth baud rate is 31250")
                    self.uart.write("Bluetooth baud rate is 31250")
                elif i == 12:
                    print("Bluetooth baud rate is 2400")
                    self.uart.write("Bluetooth baud rate is 2400")
                elif i == 13:
                    print("Bluetooth baud rate is 4800")
                    self.uart.write("Bluetooth baud rate is 4800")
        elif data == Low_Power_Query:
            if data_rx[0:5] == b'QL+00':
                print("Normal operating mode")
                self.uart.write("Normal operating mode")
            elif data_rx[0:5] == b'QL+01':
                print("Low power operation mode")
                self.uart.write("Low power operation mode")
        elif (data == Name_BLE_Query) | (data == Name_SPP_Query) | (data == ADD_Query):
            if data_rx[0:3] == b'TM+':
                print("BLE name is : ")
                self.uart.write("BLE name is : ")
                i = 3
                while chr(data_rx[i]) != '\r':
                    i = i + 1
                print("%s" % data_rx[3:i])
                self.uart.write(data_rx[3:i])
            elif data_rx[0:3] == b'TD+':
                print("SPP name is : ")
                self.uart.write("SPP name is : ")
                i = 3
                while chr(data_rx[i]) != '\r':
                    i = i + 1
                print("%s" % data_rx[3:i])
                self.uart.write(data_rx[3:i])
            elif data_rx[0:3] == b'TB+':
                print("BLE add is : ")
                self.uart.write("BLE add is : ")
                i = 3
                while chr(data_rx[i]) != '\r':
                    i = i + 1
                print("%s" % data_rx[3:i])
                self.uart.write(data_rx[3:i])
        elif (data == BLE_Switch_Query) | (data == SPP_Switch_Query):
            if data_rx[0:5] == b'T4+01':
                print("BLE to open up")
                self.uart.write("BLE to open up")
            elif data_rx[0:5] == b'T4+00':
                print("BLE to shut down")
                self.uart.write("BLE to shut down")
            elif data_rx[0:5] == b'T5+01':
                print("SPP to open up");
                self.uart.write("SPP to open up")
            elif data_rx[0:5] == b'T5+00':
                print("SPP to shut down")
                self.uart.write("SPP to shut down")
        else:
            if data_rx[0:2] == b'OK':
                return True
        if data_rx[0:3] == b'ER+':
            self.__error_out(data_rx[3] - 48)
            return False

    @staticmethod
    def __error_out(data: bytes):
        if data == 1:
            print("Incorrect data frame received")
        elif data == 2:
            print("The received command does not exist")
        elif data == 3:
            print("Received AT instruction, carriage return line feed not received")
        elif data == 4:
            print(
                "Sent instructions with parameters that are out of range or in the wrong format. Please check your AT instructions")
        elif data == 7:
            print(
                "The MCU sends data to the mobile phone, but notify is not enabled on the mobile phone. The BLE connection is successfu")
