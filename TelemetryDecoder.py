from enum import Enum
import struct


"""
Telemetry Decoding:

outputs line (str) to queue
...
reads from queue:

TelemetryDecoder:
  - SDCardTelemetryDecoder
  - RadioTelemetryDecoder
"""


class RadioPacket:
    def __init__(self,
                 data_bytes) -> None:

        self.values = struct.unpack(self.format, data_bytes)

    def __iter__(self):
        return zip(self.keys, self.values)

class PreFlightPacket(RadioPacket):
    keys = ["event",       # uint8_t   event
            "gnss_fix",    # uint8_t   gnss.fix
            "report_code", # uint8_t   cont.reportCode
            "rocketName",  # char[20?] rocketName   w
            "base_alt",    # uint16_t  baseAlt
            "gps_alt",     # uint16_t  GPSalt
            "gps_lat",     # float     GPS.location.lat
            "gps_lon",     # float     GPS.location.lng
            "num_sats"]    # uint16_t  satNum

    format = "@BBB20sHHffH"

class InFlightData(RadioPacket):
    keys = ["event",    # uint8_t event
            "fltTime",  # int16_t fltTime
            "vel",      # int16_t vel
            "alt",      # int16_t alt
            "roll",     # int16_t roll
            "off_vert", # int16_t offVert
            "accel"]    # int16_t accel

    format = "@B6H"

class InFlightMetaData(RadioPacket):
    keys = ["packetnum",    # int16_t packetnum
            "gps_alt",      # int16_t GPSalt
            "gps_lat",      # float   GPS.location.lat
            "gps_lon"]      # float   GPS.location.lon

    format = "@13B13B13B13BHHff"

class PostFlightPacket(RadioPacket):
    keys = ["event",        # uint8_t  event
            "max_alt",      # uint16_t maxAlt
            "max_vel",      # uint16_t maxVel
            "max_g",        # uint16_t maxG
            "max_gps_alt",  # uint16_t maxGPSalt
            "gps_fix",      # uint8_t  gnss.fix
            "gps_alt",      # uint16_t GPSalt
            "gps_lat",      # float    GPS.location.lat
            "gps_lon"]      # float    GPS.location.lng

    format = "@B4HBHff"


class RadioTelemetryDecoder(object):
    """
    Converts flight telemetry received over radio direct from vehicle
    into SD-card style data for sending to UI (which is wanting SD-card style)
    """

    NUM_FLIGHT_DATA_MESSAGES = 4        # each in-flight packet contains this many actual data samples
    FLIGHT_DATA_MESSAGE_LENGTH = 13     # length of each of this samples
    FLIGHT_DATA_TOTAL_LENGTH = NUM_FLIGHT_DATA_MESSAGES * FLIGHT_DATA_MESSAGE_LENGTH

    # Mapping of event number to text name:
    event_names =  ["Preflight","Liftoff","Booster Burnout","Apogee Detected","Firing Apogee Pyro"
                    "Separation Detected","Firing Mains","Under Chute","Ejecting Booster",
                    "Firing 2nd Stage","2nd Stage Ignition","2nd Stage Burnout","Firing Airstart1",
                    "Airstart 1 Ignition","Airstart 1 Burnout","Firing Airstart2","Airstart 2 Ignition",
                    "Airstart 2 Burnout","NoFire: Rotn Limit","NoFire: Alt Limit","NoFire: Rotn/Alt Lmt",
                    "Booster Apogee","Booster Apogee Fire","Booster Separation","Booster Main Deploy",
                    "Booster Under Chute","Time Limit Exceeded","Touchdown!","Power Loss! Restart",
                    "Booster Touchdown","Booster Preflight","Booster Time Limit","Booster Pwr Restart"]

    def decode(self, data_bytes) -> list | None:

        event = data_bytes[0]

        try:
            if event == 0 or event == 30:
                return [dict(PreFlightPacket(data_bytes))]
            elif event < 26:
                messages = []
                last_index = 0

                for index in range(0,
                                   self.FLIGHT_DATA_TOTAL_LENGTH,
                                   self.FLIGHT_DATA_MESSAGE_LENGTH):
                    inflight_bytes = data_bytes[index:index + self.FLIGHT_DATA_MESSAGE_LENGTH]
                    messages.append(dict(InFlightData(inflight_bytes)))

                in_flight_meta_bytes = data_bytes[self.FLIGHT_DATA_MESSAGE_LENGTH:]
                messages.append(dict(InFlightMetaData(in_flight_meta_bytes)))

            else:
                return [dict(PostFlightPacket(data_bytes))]

        except Exception:
            return None



class DecoderState(Enum):
    FLIGHT = 0
    MAXES = 1
    LAUNCH = 2
    LAND = 3
    END = 4


class SDCardTelemetryDecoder(object):
    """
    takes line of FC SD-card data and decodes it into a dictionary:
    """

    TIMESTAMP_RESOLUTION = 1000000 # timestamp least significant figure is 10e-8 seconds
    DEFAULT_ACCEL_RESOLUTION = 1024

    def __init__(self, accel_resolution: int = DEFAULT_ACCEL_RESOLUTION) -> None:

        self.state = DecoderState.FLIGHT
        self.telemetry_keys = None
        self.unique_keys = { DecoderState.FLIGHT: "fltEvents",
                             DecoderState.MAXES: "Max Baro Alt",
                             DecoderState.LAUNCH: "launch date",
                             DecoderState.LAND: "landing date",
                             DecoderState.END: "Rocket Name" }

        self.accel_resolution = accel_resolution

        self.modifiers = { "time": self.time_modifier,
                           "accelX": self.accel_modifier,
                           "accelY": self.accel_modifier,
                           "accelZ": self.accel_modifier }

    def time_modifier(self, time):
        return float(time) / self.TIMESTAMP_RESOLUTION

    def accel_modifier(self, accel):
        return float(accel) / self.accel_resolution

    @staticmethod
    def format_key(key):
        # change all keys to be consistently formatted
        return key.strip().replace(" ","_")

    def decode_line(self, line: str) -> dict | None:
        """
        decodes a line of SD-card flight telemetry

        SD-card telemetry from flight computer contains 2 types of rows:
        1) key rows, which are made up of text items and describe what's on the following lines
        2) value rows, which contain mostly numeric (but also some text) telemetry

        the number of values and their types depends on the last key row that came before it
        so we attempt to detect these key rows and based on unique items that they contain
        (there is no built-in signifier of the type, such as a row ID)
        and then we store this as the current DecoderState.

        we store the keys when we find a new key row as a list, which is then used to construct
        a message to send to the UI which can decode the dict into values to update the screen
        """

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
                    [SDCardTelemetryDecoder.format_key(key) for key in items if key.strip()]

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
        """
        maps received data line to keys from key line for sending dict to UI
        """
        try:
            telemetry_dict = {key: value for (key, value) in zip(self.telemetry_keys, values) if value.strip()}
        except Exception:
            return None

        modified_telemetry = self.apply_modifiers(telemetry_dict)

        # return a dict of all the key-value pairs in the received telemetry, ignoring all empties
        return modified_telemetry

    def apply_modifiers(self, telemetry_dict: dict) -> dict:
        """
        some values which are received from SD reading are not in a format good for
        the user interface, so we change them before sending to UI
        """
        for key in telemetry_dict:
            if key in self.modifiers:
                old_value = telemetry_dict[key]
                telemetry_dict[key] = self.modifiers[key](old_value)

        return telemetry_dict