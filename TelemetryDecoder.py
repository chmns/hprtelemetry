import csv
import os
from threading import Thread
from time import sleep
import sys
from inflection import underscore
from enum import Enum

# TEST_FILE_1 = "test_data\\test_1.txt"

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


needed:


accel display
------------
smoothHighGz

accel chart
------------
accelX,accelY,accelZ

velocity display
------------
intVel

velocity chart
------------
intVel, fusionVel, gnssSpeed, baroVel

alt display
------------
intAlt

altitude chart
------------
intAlt, fusionAlt, baroAlt, altMoveAvg, gnssAlt

roll display
------------
rollZ, offVert

display in English
------------
fltEvents, radioCode

map
------------
gnssLat,gnssLon, (as a path from start to end)

status display
------------
rocketName, time, radioPacketNum, gnssSatellites
"""

class DecoderState(Enum):
    FLIGHT = 0
    MAXES = 1
    LAUNCH = 2
    LAND = 3
    END = 4


class FlightTelemetryDecoder(object):
    """
    takes line of flight data, check CRC32 and if it valid
    decode these regular items into a dictionary:

    time: change into seconds (from millisecond?)
    smoothHighGz
    accelX,accelY,accelZ
    intVel, fusionVel, gnssSpeed, baroVel
    intAlt, fusionAlt, baroAlt, altMoveAvg, gnssAlt
    rollZ, offVert
    
    separately has callbacks for slow update items:
    rocketName,
    radioPacketNum,
    gnssSatellites,
    fltEvents, radioCode: decoded in english text
    gnssLat,gnssLon,

    local variables:
    accel_gain (depends on model of accelerometer)

            self.telemetry = {
            "time": 0,
            "smoothHighGz": 0,
            "accelX": 0,
            "accelY": 0,
            "accelZ": 0,
            "intVel": 0,
            "fusionVel": 0,
            "gnssSpeed": 0,
            "baroVel": 0,
            "intAlt": 0,
            "fusionAlt": 0,
            "baroAlt": 0,
            "altMoveAvg": 0,
            "gnssAlt": 0,
            "rollZ": 0,
            "offVert": 0
        }
    """
    def __init__(self, name_callback: callable = None):
        self.name_callback = name_callback
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
        return underscore(key.strip()).replace(" ","_")

    def decode_line(self, line: str):
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

        # vast majority of lines will be raw telemetry so check for this first:
        if self.state == DecoderState.FLIGHT and items[0].isnumeric:
            self.decode_telemetry_values(items)
        
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
                    items[0] = "time"
                    self.name_callback(items[0])
                    
                # reformat keys and remove empty keys, then store for decoding:
                self.telemetry_keys =  \
                    [FlightTelemetryDecoder.format_key(key) for key in items if key.strip()]
                return # return and await next line to decode it

        # if it's not flight telemetry, and it's not a key-row, then we can assume it's another
        # row of telemetry (like launch/land/flight-summary)
        self.decode_telemetry_values(items)

    def decode_telemetry_values(self, values):
        # return a dict of all the key-value pairs in the received telemetry, ignoring all empties
        return {key: value for (key, value) in zip(self.telemetry_keys, values) if value.strip()}

# class GroundTelemetryDecoder(Thread):
#     def __init__(self,
#                  prelaunch_callback: callable = None,
#                  message_callback: callable = None) -> None:
#         super().__init__()
#         self.prelaunch_callback = prelaunch_callback
#         self.message_callback = message_callback
#         self.file = None

#     @staticmethod
#     def decodeMessage(message) -> (dict | None):
#         try:
#             message_dict = {
#                 "event": message[0],
#                 "time": float(message[1]),
#                 "acceleration": float(message[2]),
#                 "velocity": float(message[3]),
#                 "altitude": float(message[4]),
#                 "spin": float(message[5]),
#                 "tilt": float(message[6]),
#                 "gpsAlt": float(message[7]),
#                 "gpsLat": float(message[8]),
#                 "gpsLon": float(message[9]),
#                 "signalStrength": float(message[10]),
#                 "packetNum": message[11]
#             }
#         except:
#             return None
#         return message_dict

#     @staticmethod
#     def decodePrelaunch(message) -> (dict | None):
#         try:
#             prelaunch_dict = {
#                 "RocketName": message[1],
#                 "Continuity": int(message[2]),
#                 "GPSlock": bool(message[3]),
#                 "BaseAlt": float(message[4]),
#                 "gpsAlt": float(message[5]),
#                 "gpsLat": float(message[6]),
#                 "gpsLon": float(message[7]),
#             }
#         except:
#             return None
#         sleep(0.5)
#         return prelaunch_dict

#     @staticmethod
#     def decodePostflight(message) -> (dict | None):
#         try:
#             postflight_dict = {
#                 "rocketName": message[0],
#                 "lastEvent": message[1],
#                 "maxAlt": message[2],
#                 "maxVel": message[3],
#                 "maxG": message[4],
#                 "maxGPSalt": message[5],
#                 "gpsLock": message[6],
#                 "gpsALt": message[7],
#                 "gpsLatitude": message[8],
#                 "gpsLongitude": message[9]
#             }
#         except:
#             return None
#         return postflight_dict

#     def run(self):
#         if self.file is None:
#             print("No telemetry file selected, can't run")
#             return

#         # pwd = os.path.dirname(__file__)
#         # abs_file_path = os.path.join(pwd, rel_path)

#         # if getattr(sys, 'frozen', False):
#         #     abs_file_path = os.path.join(sys._MEIPASS, rel_path)
#         # else:
#         #     abs_file_path = os.path.join(pwd, rel_path)

#         # with open(self.file, 'rt') as csv_file:
#         csv_reader = csv.reader(self.file, delimiter=',')

#         for row in csv_reader:
#             if not row[0] == "Telemetry Rocket Recorder":
#                 print("Invalid telemetry file")
#                 return
#             else:
#                 break

#         for row in csv_reader:
#             self.prelaunch_callback(TestTelemetry.decodePrelaunch(row))
#             break

#         for row in csv_reader:
#             if row[0].isnumeric() and self.message_callback is not None:
#                 if int(row[0]) > 0 and int(row[0]) < 8:
#                     # print(row)
#                     self.message_callback(TestTelemetry.decodeMessage(row))
#                     # print(TestTelemetry.decodeMessage(row))
#                     sleep(0.05)
                

if __name__ == "__main__":
    test = TestTelemetry(print)
    test.start()
                    



                    
        # else:
        #     if "Max Baro Alt" in items:
        #         self.state = DecoderState.MAXES
        #         # in addition to setting the decoder state, we also store the keys:
                

        #     elif "launch date" in items:
        #         self.state = DecoderState.LAUNCH
        #         self.set_keys(items)
                
        #     elif "landing date" in items:
        #         self.state = DecoderState.LAND
        #         self.set_keys(items)
                
        #     elif "Rocket Name" in items:
        #         self.state = DecoderState.END
        #         self.set_keys(items)
                
        #     elif "fltEvents" in items:
        #         self.state = DecoderState.FLIGHT
        #         self.rocket_name = items[0]
        #         # rocket name is the only time that a value is stored in the position of a key
        #         # so we store the name and set the key to what it really signifies: time
        #         items[0] = "time"
        #         self.set_keys(items)

        #     else:
        #         # if we don't find a key row, assume it's telemetry: