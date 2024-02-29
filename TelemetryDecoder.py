import os
from threading import Thread
from time import sleep
import sys
from inflection import underscore
from enum import Enum

TEST_MESSAGE_INTERVAL = 0.05

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
    def __init__(self, name_callback: callable = None, message_callback: callable = None):
        self.name_callback = name_callback
        self.message_callback = message_callback

        self.state = DecoderState.FLIGHT
        self.telemetry_keys = None
        self.unique_keys = { DecoderState.FLIGHT: "fltEvents",
                             DecoderState.MAXES: "Max Baro Alt",
                             DecoderState.LAUNCH: "launch date",
                             DecoderState.LAND: "landing date",  
                             DecoderState.END: "Rocket Name" }
        
    @staticmethod
    def format_key(key):
        # change all keys to be consistently formatted
        # return underscore(key.strip()).replace(" ","_")
        return key.strip().replace(" ","_")

    def decode_line(self, line: str) -> None:
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
            return

        # vast majority of lines will be raw telemetry so check for this first:
        if self.state == DecoderState.FLIGHT and items[0].isnumeric():
            self.message_callback(self.decode_telemetry_values(items))
            return
        
        # but if not raw telemetry, we check to see if there's a row of keys instead
        # the only way to know what a line means is based on unique items that we can
        # find in key-rows
        for state, unique_key in self.unique_keys.items():
            if unique_key in items:
                self.state = state

                # item 0 of FLIGHT key-row is actually name of rocket which complicates things
                # as its column actually refers to time, not name. So we replace the key name
                # and fire a separate callback
                if state == DecoderState.FLIGHT:
                    self.name_callback(items[0])
                    items[0] = "time"
                    
                # reformat keys and remove empty keys, then store for decoding:
                self.telemetry_keys =  \
                    [FlightTelemetryDecoder.format_key(key) for key in items if key.strip()]
                return # return and await next line to decode it

        # if it's not flight telemetry, and it's not a key-row, then we can assume it's another
        # row of telemetry (like launch/land/flight-summary)
        self.message_callback(self.decode_telemetry_values(items))

    def decode_telemetry_values(self, values) -> dict | None:
        dict = {key: value for (key, value) in zip(self.telemetry_keys, values) if value.strip()}
        # return a dict of all the key-value pairs in the received telemetry, ignoring all empties
        return dict

class TelemetryTester(object):
    def __init__(self, filepath) -> None:
        assert filepath is not None
        self.rel_path = filepath
        self.decoder = FlightTelemetryDecoder()

    def start(self):
        test_thread = Thread(target=self.read_file)
        test_thread.start()
    
    def read_file(self):
        pwd = os.path.dirname(__file__)
        # abs_file_path = os.path.join(pwd, self.rel_path)

        if getattr(sys, 'frozen', False):
            abs_file_path = os.path.join(sys._MEIPASS, self.rel_path)
        else:
            abs_file_path = os.path.join(pwd, self.rel_path)

        with open(abs_file_path, 'rt') as test_telemetry:
            for line in test_telemetry:
                self.decoder.decode_line(line)
                sleep(TEST_MESSAGE_INTERVAL)

if __name__ == "__main__":
    test = TelemetryTester("test_data\\FLIGHT10-short.csv")
    test.decoder.name_callback = print
    test.decoder.message_callback = print
    test.start()