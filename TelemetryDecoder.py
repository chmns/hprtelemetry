from threading import Thread, Event
from tkinter import StringVar, BooleanVar
from time import sleep
import sys
from enum import Enum
import queue

import sys
import glob
import serial

TIMESTAMP_RESOLUTION = 10000000 # timestamp least significant figure is 10e-8 seconds
DEFAULT_BAUD = 57600
DEFAULT_TIMEOUT = 1 # seconds
TEST_MESSAGE_INTERVAL = 0.05

BAUD_RATES = [1200, 1800, 2400, 4800, 9600, 19200, 38400, 57600, 115200]

"""
Telemetry Decoding:

TelemetryReader:
1) TelemetryFileReader (from SD card file or backup)
2) TelemetryRadioReader (from Radio)

outputs line (str) to queue
...
reads from queue:

TelemetryDecoder:
FlightTelemetryDecoder
GroundTelemetryDecoder

outputs:

TelemetryDictionary

to

telemetry.py UI

Flight data available:

accelX,accelY,accelZ,   # raw accelerometer values that need multiplier applied depending on model
gyroX,gyroY,gyroZ,  # raw gyro values as above
highGx,highGy,highGz,   # not sure
smoothHighGz,   # presumably filtered from high Gz
rollZ,yawY,pitchX,  # integrated gyro values? or from fusion algo?
offVert,    # pitch angle deviation from vertical
intVel,intAlt,  # integrated velocity and altitude?
fusionVel,fusionAlt,    # velocity and altitude from fusion algo?
fltEvents,  # bitfield of flight status
radioCode,  # like 'event'
pyroCont,pyroFire,pyroPin, # pyro status
baroAlt,altMoveAvg,baroVel,baroPress,baroTemp, #  barometer data
battVolt,   # battery voltage
magX,magY,magZ,     # magnetometer values (presumably need multiplier)
gnssLat,gnssLon,gnssSpeed,gnssAlt,gnssAngle,gnssSatellites,     # raw GPS data
radioPacketNum      # which packet this data came from (multiple messages can share a packet)
"""

class DecoderState(Enum):
    FLIGHT = 0
    MAXES = 1
    LAUNCH = 2
    LAND = 3
    END = 4


class FlightTelemetryDecoder(object):
    """
    takes line of flight data and decodes it into a dictionary:
    """
    def __init__(self) -> None:

        self.state = DecoderState.FLIGHT
        self.telemetry_keys = None
        self.unique_keys = { DecoderState.FLIGHT: "fltEvents",
                             DecoderState.MAXES: "Max Baro Alt",
                             DecoderState.LAUNCH: "launch date",
                             DecoderState.LAND: "landing date",
                             DecoderState.END: "Rocket Name" }

        self.modifiers = { "time": lambda time : time / TIMESTAMP_RESOLUTION }


    @staticmethod
    def format_key(key):
        # change all keys to be consistently formatted
        return key.strip().replace(" ","_")

    def decode_line(self, line: str) -> dict | None:
        """
        decodes a line of flight telemetry

        flight telemetry contains 2 types of rows:
        1) key rows, which are made up of text items and describe what's on the following lines
        2) value rows, which contain mostly numeric (but also some text) telemetry

        the number of values and their types depends on the last key row that came before it
        so we attempt to detect these key rows and based on unique items that they contain
        (there is no built-in signifier of the type, such as a row ID)
        and then we store this as the current DecoderState.

        we store the keys when we find a new key row as a list, which is then used to construct
        a message to send to the UI which can decode the dict into values to update the screen
        """

        # ideally we will have CRC32 check for each line before this, so we can guarantee
        # that the data is good, but that can come at a later time

        items = line.split(",")
        if len(items) < 2:
            return None

        # vast majority of lines will be raw telemetry so check for this first:
        if self.state == DecoderState.FLIGHT and items[0].isnumeric():
            return self.decode_telemetry_values(items)

        # but if not raw telemetry, we check to see if there's a row of keys instead
        # the only way to know what a line means is based on unique items that we can
        # find in key-rows
        for state, unique_key in self.unique_keys.items():
            if unique_key in items:
                self.state = state

                # reformat keys and remove empty keys, then store for decoding:
                self.telemetry_keys =  \
                    [FlightTelemetryDecoder.format_key(key) for key in items if key.strip()]

                # item 0 of FLIGHT key-row is actually name of rocket which complicates things
                # as its column actually refers to time, not name. So we return name only.
                if state == DecoderState.FLIGHT:
                    name = items[0]
                    self.telemetry_keys[0] = "time"
                    return {"name": name}
                else:
                    return None # return and await next line to decode it

        # if it's not flight telemetry, and it's not a key-row, then we can assume it's another
        # row of telemetry (like launch/land/flight-summary)
        return self.decode_telemetry_values(items)

    def decode_telemetry_values(self, values) -> dict | None:
        try:
            telemetry_dict = {key: value for (key, value) in zip(self.telemetry_keys, values) if value.strip()}
        except Exception:
            return None

        # return a dict of all the key-value pairs in the received telemetry, ignoring all empties
        return telemetry_dict

class TelemetryReader(object):
    def __init__(self,
                 queue: queue.Queue = None) -> None:
        # assert queue is not None
        self.queue = queue
        self.running = Event()
        self.decoder = FlightTelemetryDecoder()
        self.thread = None

    def start(self) -> None:
        self.running.set()
        self.thread = Thread(target=self.__run__, args=(self.queue,self.running))
        self.thread.start()

    def stop(self) -> None:
        self.running.clear()
        if self.thread is not None:
            self.thread.join()

    def __run__(self):
        pass


class TelemetrySerialReader(TelemetryReader):
    def __init__(self,
                 queue: queue.Queue = None,
                 serial_port = None,
                 baud_rate = DEFAULT_BAUD,
                 timeout = DEFAULT_TIMEOUT) -> None:

        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.timeout = timeout
        TelemetryReader.__init__(self, queue)

    def __run__(self, message_queue, running):
        assert self.serial_port is not None
        assert self.serial_port != ""

        port = None

        try:
            port = serial.Serial(port=self.serial_port,
                                 baudrate=self.baud_rate,
                                 timeout=self.timeout)
        except:
            print(f"Could not open serial port: {self.serial_port}")
            return
        finally:
            port.close()

        while running.is_set():
            try:
                telemetry_dict = self.decoder.decode_line(port.readline().decode("Ascii"))
                if telemetry_dict is not None:
                    message_queue.put(telemetry_dict)
            except:
                pass

        running.clear()
        port.close()


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


class TelemetryFileReader(TelemetryReader):
    def __init__(self,
                 queue: queue.Queue = None) -> None:

        self.filename = None
        TelemetryReader.__init__(self, queue)

    def __run__(self, message_queue, running):
        assert self.filename is not None

        print(f"Reading telemetry file {self.filename}")

        last_timestamp = 0

        try:
            with open(self.filename, 'rt') as telemetry_file:
                for line in telemetry_file:
                    if not running.is_set():
                        return

                    telemetry_dict = self.decoder.decode_line(line)

                    if telemetry_dict is None:
                        continue

                    message_queue.put(telemetry_dict)

                    if "time" in telemetry_dict:
                        timestamp = int(telemetry_dict["time"])
                        delta = timestamp - last_timestamp
                        last_timestamp = timestamp
                        sleep(delta / TIMESTAMP_RESOLUTION)

        except IOError:
            print(f"Cannot read file: {self.filename}")

        finally:
            running.clear()

        print(f"Finished reading file {self.filename}")



class TelemetryTestSender(TelemetryReader):
    def __init__(self, _) -> None:

        self.filename = None
        self.serial_port = "COM3"
        TelemetryReader.__init__(self, None)

    def __run__(self, message_queue, running):
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
            port.close()
            return

        print(f"Opened port {self.serial_port}")

        try:
            with open(self.filename, 'rt') as telemetry_file:
                for line in telemetry_file:
                    if not running.is_set():
                        print("stopping")
                        return

                    telemetry_dict = self.decoder.decode_line(line)

                    buffer = bytes(line, "ascii")
                    port.write(buffer)

                    if "time" in telemetry_dict:
                        timestamp = int(telemetry_dict["time"])
                        delta = timestamp - last_timestamp
                        last_timestamp = timestamp
                        sleep(delta / TIMESTAMP_RESOLUTION)
                    else:
                        sleep(0.01)

        except IOError:
            print(f"Cannot read file: {self.filename}")

        finally:
            running.clear()
            port.close()

        print(f"Finished reading file {self.filename} out of serial port {self.serial_port}")
