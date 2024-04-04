from threading import Thread, Event
from time import sleep
import sys
import queue
import sys
import glob
import serial
from TelemetryDecoder import SDCardTelemetryDecoder, RadioTelemetryDecoder


class TelemetryReader(object):
    """
    Base class for Telemetry receivers
    """

    def __init__(self,
                 queue: queue.Queue = None,
                 bytes_received_queue: queue = None,
                 name: str = "") -> None:
        # assert queue is not None
        self.queue = queue
        self.bytes_received_queue = bytes_received_queue
        self.running = Event()
        self.decoder = SDCardTelemetryDecoder()
        self.thread = None
        self.name = name

    def start(self) -> None:
        self.running.set()
        self.thread = Thread(target=self.__run__, args=(self.queue,self.bytes_received_queue,self.running), name=self.name)
        self.thread.start()

    def stop(self) -> None:
        self.running.clear()
        if self.thread is not None:
            print(f"Stopping thread: {self.thread}")
            self.thread.join()

    def __run__(self):
        pass


class TelemetrySerialReader(TelemetryReader):
    """
    Base class for readers that read from serial port and save to backup file
    """

    DEFAULT_BAUD = 57600
    DEFAULT_TIMEOUT = 1 # seconds
    BAUD_RATES = [1200, 1800, 2400, 4800, 9600, 19200, 38400, 57600, 115200]

    def __init__(self,
                 queue: queue.Queue = None,
                 bytes_received_queue: queue.Queue = None,
                 serial_port = None,
                 baud_rate = DEFAULT_BAUD,
                 timeout = DEFAULT_TIMEOUT) -> None:

        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.filename = None
        TelemetryReader.__init__(self, queue, bytes_received_queue)

    def __run__(self,
                message_queue: queue.Queue,
                bytes_received_queue: queue.Queue,
                running):

        assert self.serial_port is not None
        assert self.serial_port != ""

        port = None
        file = None

        try:
            port = serial.Serial(port=self.serial_port,
                                 baudrate=self.baud_rate,
                                 timeout=self.timeout)
            print(f"Successfully opened port {self.serial_port}")
        except:
            print(f"Could not open serial port: {self.serial_port}")
            return

        while self.running.is_set():
            telemetry = self.__read_port__(port,
                                           message_queue,
                                           bytes_received_queue)

            telemetry_dict = self.decoder.decode(telemetry)

            if telemetry_dict is not None:
                message_queue.put((telemetry_dict, self.decoder.state))

        if file is not None:
            file.close()

        if port is not None:
            port.close()

        running.clear()



class RadioTelemetryReader(TelemetrySerialReader):
    """
    Class for reading Radio telemetry sent by Flight Computer over RFD900 or other serial radio bridge
    """

    def __init__(self, *kargs) -> None:
        self.decoder = RadioTelemetryDecoder()
        TelemetrySerialReader.__init__(self, kargs)

    def __read_port__(self,
                      port: serial.Serial,
                      message_queue: queue.Queue,
                      bytes_received_queue: queue.Queue):
        try:
            data_bytes = port.read_all()
            bytes_received_queue.put(len(data_bytes))
        except:
            print(f"Error reading from port: {self.serial_port}")

        if file is None and self.filename is not None: # file isn't open but user has added backup file
            try:
                file = open(self.filename, 'a') # open with 'a' mode to append to existing file so we dont over-write
            except:
                print(f"Couldn't open file {self.filename}")
                file = None
            else:
                print(f"Open file for writing backup to: {self.filename}")

        if file is not None:
            try:
                file.write(data_bytes)
            except:
                print(f"Couldn't write backup data to file {self.filename}")




class SDCardSerialReader(TelemetrySerialReader):
    """
    Class for reading Flight Computer SD-Card telemetry
    """
    def __init__(self, *kargs) -> None:

        self.decoder = SDCardTelemetryDecoder()
        TelemetrySerialReader.__init__(self, kargs)

    def __read_port__(self,
                      port: serial.Serial,
                      message_queue: queue.Queue,
                      bytes_received_queue: queue.Queue) -> None:
        try:
            line = port.readline().decode("Ascii")
            bytes_received_queue.put(len(line))
        except:
            print(f"Error reading from port: {self.serial_port}")

        if file is None and self.filename is not None: # file isn't open but user has added backup file
            try:
                file = open(self.filename, 'a') # open with 'a' mode to append to existing file so we dont over-write
                file.write("\n") # ensure we start on a new line
            except:
                print(f"Couldn't open file {self.filename}")
                file = None
            else:
                print(f"Open file for writing backup to: {self.filename}")

        if file is not None:
            try:
                file.write(line)
            except:
                print(f"Couldn't write line to file {self.filename}")

        return line


    def available_ports(self) -> list:
        """
        returns a list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                serial_port = serial.Serial(port)
                serial_port.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result


class SDCardFileReader(TelemetryReader):
    def __init__(self,
                 queue: queue.Queue = None,
                 bytes_received_queue: queue.Queue = None) -> None:

        self.filename = None
        TelemetryReader.__init__(self, queue, bytes_received_queue)

    def __run__(self,
                message_queue,
                bytes_received_queue,
                running) -> None:

        assert self.filename is not None

        print(f"Reading telemetry file {self.filename}")

        last_timestamp = 0

        try:
            with open(self.filename, 'rt') as telemetry_file:
                for line in telemetry_file:
                    if not running.is_set():
                        return

                    bytes_received_queue.put(len(line))
                    telemetry_dict = self.decoder.decode_line(line)


                    if telemetry_dict is None:
                        continue

                    message_queue.put((telemetry_dict, self.decoder.state))

                    if "time" in telemetry_dict:
                        timestamp = float(telemetry_dict["time"])
                        sleep(timestamp - last_timestamp)
                        last_timestamp = timestamp

        except IOError:
            print(f"Cannot read file: {self.filename}")

        finally:
            running.clear()

        print(f"Finished reading file {self.filename}")