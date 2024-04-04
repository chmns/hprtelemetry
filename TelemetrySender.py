from TelemetryReader import TelemetryReader
from time import sleep
import serial

class TelemetryTestSender(TelemetryReader):
    TEST_MESSAGE_INTERVAL = 0.05

    def __init__(self) -> None:

        self.filename = None
        self.serial_port = "COM3"
        TelemetryReader.__init__(self, None)

    def __run__(self,
                message_queue,
                bytes_received_queue,
                running) -> None:

        assert self.filename is not None
        assert self.serial_port is not None

        print(f"Reading telemetry file {self.filename} to write out of {self.serial_port}")

        last_timestamp = 0

        port = None

        try:
            port = serial.Serial(port=self.serial_port,
                                 baudrate=57600,
                                 timeout=1)
        except:
            print(f"Test sender could not open serial port: {self.serial_port}")
            return

        print(f"Opened port {self.serial_port}")

        try:
            with open(self.filename, 'rt') as telemetry_file:
                for line in telemetry_file:
                    if not running.is_set():
                        return

                    telemetry_dict = self.decoder.decode_line(line)

                    buffer = bytes(line, "ascii")
                    port.write(buffer)

                    if telemetry_dict is None:
                        continue

                    if "time" in telemetry_dict:
                        timestamp = float(telemetry_dict["time"])
                        sleep(timestamp - last_timestamp)
                        last_timestamp = timestamp
                    else:
                        sleep(0.01)

        except IOError:
            print(f"Cannot read file: {self.filename}")

        finally:
            running.clear()
            port.close()

        print(f"Finished reading file {self.filename} out of serial port {self.serial_port}")
