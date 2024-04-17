from threading import Thread, Event
from time import sleep
import sys
import queue
import sys
import glob
import serial
from time import monotonic
from collections import namedtuple
from TelemetryDecoder import SDCardTelemetryDecoder, RadioTelemetryDecoder

Message = namedtuple("message", ["telemetry", "decoder_state", "local_time", "total_bytes", "total_messages"])

class TelemetryReader(object):
    """
    Base class for Telemetry receivers

    Reads telemetry from a source (file, radio etc) and outputs to messages queue for the UI in dict format
    """

    def __init__(self,
                 queue: queue.Queue = None,
                 name: str = "") -> None:
        # assert queue is not None
        self.queue = queue
        self.running = Event()
        self.decoder = None
        self.thread = None
        self.name = name
        self.bytes_received = 0
        self.messages_decoded = 0
        self.print_received = True

    def start(self) -> None:
        self.running.set()
        self.thread = Thread(target=self.__run__, args=(self.queue,self.running), name=self.name)
        self.thread.start()

    def stop(self) -> None:
        self.running.clear()
        if self.thread is not None:
            print(f"Stopping thread: {self.name} ({self.thread})")
            self.thread.join()

    def __run__(self):
        pass


class TelemetrySerialReader(TelemetryReader):
    """
    Base class for readers that read from serial port and save to backup file
    """
    BAUD_RATES = [1200, 1800, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
    DEFAULT_BAUD = 57600
    DEFAULT_TIMEOUT = 1 # seconds

    def __init__(self,
                 queue: queue.Queue = None,
                 serial_port = None,
                 baud_rate = DEFAULT_BAUD,
                 timeout = DEFAULT_TIMEOUT) -> None:

        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.filename = None
        self.read = None
        TelemetryReader.__init__(self, queue)

    def __run__(self,
                message_queue: queue.Queue,
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
        except Exception as error:
            print(f"Could not open serial port: {self.serial_port}\n{str(error)}")
            return

        while self.running.is_set():
            telemetry_bytes = None

            try:
                telemetry_bytes = self.read(port)

                if len(telemetry_bytes) == 0:
                    sleep(0.01)
                    continue
                else:
                    self.bytes_received += len(telemetry_bytes) # keep track of total amount of data we got since start

                    if self.print_received:
                        print(f"{len(telemetry_bytes):>6} bytes: {telemetry_bytes.hex(' ')}  ({self.bytes_received} bytes total)") # for debug

            except Exception as error:
                print(f"Error reading from port: {self.serial_port}\n{str(error)}")
                print(f"{telemetry_bytes = }")

            if file is None and self.filename is not None: # file isn't open but user has added backup file during running
                try:
                    file = open(self.filename, 'wb') # open with 'wb' write binary mode - will overwrite any existing file
                except Exception as error:
                    print(f"Couldn't open file {self.filename}")
                    file = None
                else:
                    print(f"Open file for writing backup to: {self.filename}")

            if file is not None:
                try:
                    file.write(telemetry_bytes)
                except Exception as error:
                    print(f"Couldn't write backup data to file {self.filename}\n{str(error)}")

            # We still send message to UI even if no telemetry is decoded from packet (maybe is corrupt)
            # So start with empty dict
            received_telemetry = {}
            received_telemetry_messages = []

            try:
                received_telemetry_messages = self.decoder.decode(telemetry_bytes)
            except Exception as error:
                print(f"Error decoding data from: {self.serial_port}\n{str(error)}")

            if received_telemetry_messages is not None:
                for message in received_telemetry_messages:
                    self.messages_decoded += 1
                    received_telemetry |= message

            message_queue.put(Message(received_telemetry,
                                      self.decoder.state,
                                      monotonic(),
                                      self.bytes_received,
                                      self.messages_decoded))

        if file is not None:
            file.close()

        if port is not None:
            port.close()

        running.clear()

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

class RadioTelemetryReader(TelemetrySerialReader):
    """
    Class for reading Radio telemetry sent by Flight Computer over RFD900 or other serial radio bridge
    """

    SYNC_WORD = bytes.fromhex("A5A5A5A5")
    MAX_PACKET_LENGTH = 74

    def __init__(self, *kargs) -> None:
        TelemetrySerialReader.__init__(self, *kargs)
        self.decoder = RadioTelemetryDecoder()
        self.read = lambda port: serial.Serial.read_until(port,
                                                          self.SYNC_WORD,
                                                          self.MAX_PACKET_LENGTH)


class SDCardSerialReader(TelemetrySerialReader):
    """
    Class for reading Flight Computer SD-Card-style telemetry over a serial port
    """
    def __init__(self, *kargs) -> None:
        TelemetrySerialReader.__init__(self, *kargs)
        self.decoder = SDCardTelemetryDecoder()
        self.read = serial.Serial.readline


class SDCardFileReader(TelemetryReader):
    """
    Class for reading Flight Computer SD-Card telemetry from a file
    """
    def __init__(self, queue: queue.Queue = None) -> None:

        TelemetryReader.__init__(self, queue)
        self.filename = None
        self.decoder = SDCardTelemetryDecoder()

    def __run__(self, message_queue, running) -> None:

        assert self.filename is not None

        print(f"Reading telemetry file {self.filename}")

        last_timestamp = 0

        try:
            with open(self.filename, 'rt') as telemetry_file:
                for line in telemetry_file:
                    if not running.is_set():
                        return
                    self.bytes_received += len(line)
                    self.messages_decoded += 1

                    telemetry_dict = self.decoder.decode(line)

                    if telemetry_dict is None:
                        continue

                    message_queue.put(Message(telemetry_dict,
                                            self.decoder.state,
                                            monotonic(),
                                            self.bytes_received,
                                            self.messages_decoded))

                    if "time" in telemetry_dict:
                        timestamp = float(telemetry_dict["time"])
                        sleep(timestamp - last_timestamp)
                        last_timestamp = timestamp

        except IOError:
            print(f"Cannot read file: {self.filename}")

        finally:
            running.clear()

        print(f"Finished reading file {self.filename}")