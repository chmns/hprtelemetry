from enum import StrEnum
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
ENDIANNESS = "<"
FLOATS_FORMAT = "{:.6f}"

class RadioPacket(object):
    def __init__(self,
                 data_bytes: bytes) -> None:
        self.values = list(struct.unpack(self.format, data_bytes))

    def as_dict(self):
        zipped = zip(self.keys, self.values)
        return dict(zipped)

class ErrorPacket(object):
    def __init__(self, event) -> None:
        self.values["event"] = event

class PreFlightPacket(RadioPacket):
    keys = ["event",          # uint8_t   event
            "preGnssFix",     # uint8_t   gnss.fix # interpret as bool
            "cont",           # uint8_t   cont.reportCode
            "name",           # char[20]  rocketName
            "baroAlt",        # int16_t   baseAlt
            "preGnssAlt",     # int16_t   GPSalt
            "preGnssLat",     # float     GPS.location.lat
            "preGnssLon",     # float     GPS.location.lng
            "gnssSatellites", # uint16_t  satNum
            "callsign"]       # char[6]   callsign

    format = f"{ENDIANNESS}B?B20shhffH6s"

class InFlightData(RadioPacket):
    keys = ["event",     # uint8_t  event
            "time",      # uint16_t fltTime
            "fusionVel", # int16_t  vel
            "fusionAlt", # int16_t  alt
            "spin",      # int16_t  roll
            "offVert",   # int16_t  offVert
            "accelZ"]    # int16_t  accel

    format = f"{ENDIANNESS}BHhhhhh"

class InFlightMetaData(RadioPacket):
    keys = ["radioPacketNum", # int16_t packetnum
            "gnssAlt",        # int16_t GPSalt
            "gnssLat",        # float   GPS.location.lat
            "gnssLon",        # float   GPS.location.lon
            "callsign"]       # char[6] callsign

    format = f"{ENDIANNESS}HHff6s"

class PostFlightPacket(RadioPacket):
    keys = ["event",        # uint8_t  event
            "maxAlt",       # uint16_t maxAlt
            "maxVel",       # uint16_t maxVel
            "maxG",         # uint16_t maxG
            "maxGnssAlt",   # uint16_t maxGPSalt
            "postGnssFix",  # uint8_t  gnss.fix
            "postGnssAlt",  # uint16_t GPSalt
            "postGnssLat",  # float    GPS.location.lat
            "postGnssLon",  # float    GPS.location.lng
            "callsign"]     # char[6] callsign

    format = f"{ENDIANNESS}B4HBHff6s"

class DecoderState(StrEnum):
    OFFLINE = "Offline"
    PREFLIGHT = "Preflight"
    INFLIGHT = "Inflight"
    MAXES = "Maximums"
    LAUNCH = "Minimums"
    LAND = "Landed"
    POSTFLIGHT = "Postflight"
    ERROR = "Error"

class TelemetryDecoder(object):
    def __init__(self):
        self.state = DecoderState.PREFLIGHT
        self.modifiers = {}

    def decode(self, line: str) -> dict | None:
        return None

    def apply_modifiers(self, telemetry_dict: dict) -> dict:
        """
        some values which are received from SD reading are not in a format good for
        the user interface, so we change them before sending to UI
        """
        for key in telemetry_dict.keys():
            if key in self.modifiers:
                old_value = telemetry_dict[key]
                telemetry_dict[key] = self.modifiers[key](old_value)

        return telemetry_dict

    def floats_modifier(self, coord: float) -> str:
        return FLOATS_FORMAT.format(coord)


class RadioTelemetryDecoder(TelemetryDecoder):
    """
    Converts flight telemetry received over radio direct from vehicle
    into dictionaries for sending to UI.
    decode() is making from binary radio into SD-card style CSV (which
    can be save to CSV file)
    then modify() changes this to be appropriate for the UI
    """

    NUM_FLIGHT_DATA_MESSAGES = 4        # each in-flight packet contains this many actual data samples
    FLIGHT_DATA_MESSAGE_LENGTH = 13     # length of each of this samples
    FLIGHT_DATA_TOTAL_LENGTH = NUM_FLIGHT_DATA_MESSAGES * FLIGHT_DATA_MESSAGE_LENGTH
    SYNC_WORD_LENGTH = 4

    ACCEL_MULTIPLIER = 0.029927521
    OFFVERT_MULTIPLIER = 0.1

    # Mapping of event number to text name:
    event_names =  ["Preflight","Liftoff","Booster Burnout","Apogee Detected","Firing Apogee Pyro",
                    "Separation Detected","Firing Mains","Under Chute","Ejecting Booster",
                    "Firing 2nd Stage","2nd Stage Ignition","2nd Stage Burnout","Firing Airstart1",
                    "Airstart 1 Ignition","Airstart 1 Burnout","Firing Airstart2","Airstart 2 Ignition",
                    "Airstart 2 Burnout","NoFire: Rotn Limit","NoFire: Alt Limit","NoFire: Rotn/Alt Lmt",
                    "Booster Apogee","Booster Apogee Fire","Booster Separation","Booster Main Deploy",
                    "Booster Under Chute","Time Limit Exceeded","Landed","Power Loss! Restart",
                    "Booster Landed","Booster Preflight","Booster Time Limit","Booster Pwr Restart"]

    cont_names = ["No Pyros Detected", "No Continuity Pyro 1", "No Continuity Pyro 2", "No Continuity Pyro 3",
                  "No Continuity Pyro 4", "All 3 Pyros Detected", "All 4 Pyros Detected", "Pyro Apogee Only",
                  "Pyro Mains Only", "Pyro Mains & Apogee"]


    def __init__(self):
        TelemetryDecoder.__init__(self)
        self.modifiers = { "name" : self.name_modifier,
                           "callsign" : self.callsign_modifier,
                           "accelZ" : self.accel_modifier,
                           "offVert" : self.offvert_and_spin_modifier,
                           "spin" : self.offvert_and_spin_modifier}

        self.floats = ["preGnssLat",  "preGnssLon",
                       "gnssLat",     "gnssLon",
                       "postGnssLat", "postGnssLon"]

    def name_modifier(self, name: bytes) -> str:
        """
        Removes extra or bad characters from name
        """
        return name.decode("ascii").strip().rstrip('\x00')

    def callsign_modifier(self, callsign: bytes) -> str:
        """
        Removes extra or bad characters from callsign
        """
        return callsign.decode("ascii").strip()

    def accel_modifier(self, accel: float) -> float:
        return accel * self.ACCEL_MULTIPLIER

    def offvert_and_spin_modifier(self, offvert: float) -> float:
        return offvert * self.OFFVERT_MULTIPLIER

    def add_formatted_floats(self, message):
        """
        For each floating point number in the telemetry it adds
        a new key with "string" on the end of the name, and the
        float is formatted into string of fixed length (for
        displaying on UI)
        """
        for key, value in message.items():
            if key in self.floats:
                message[f"{key}String"] = self.floats_modifier(value)

    def generate_float_strings(self, telemetry: dict):
        """
        Adds an additional pre-formtted float (as str type) to
        telemetry for every named float
        """
        float_strings = {}

        for key, value in telemetry.items():
            if key in self.floats:
                float_strings[f"{key}String"] = self.gnss_coords_modifier(value)

        return float_strings

    def decode(self, data_bytes) -> list | None:
        """
        Takes buffer of bytes and converts into a
        list of telemetry dictionaries. Pre and post
        packets just have 1 piece of telemetry inside
        each inflight packet has 4 samples + metadata
        so for this we get 5 dictionarys
        """
        # work out state from event byte:
        event = data_bytes[0]

        try:
            if event == 0 or event == 30:
                self.state = DecoderState.PREFLIGHT
                return [PreFlightPacket(data_bytes).as_dict()]

            elif event < 26:
                self.state = DecoderState.INFLIGHT

                messages = []

                for index in range(0,
                                   self.FLIGHT_DATA_TOTAL_LENGTH,
                                   self.FLIGHT_DATA_MESSAGE_LENGTH):

                    inflight_bytes = data_bytes[index:index + self.FLIGHT_DATA_MESSAGE_LENGTH]
                    messages.append(InFlightData(inflight_bytes).as_dict())

                in_flight_meta_bytes = data_bytes[self.FLIGHT_DATA_TOTAL_LENGTH:]
                messages.append(InFlightMetaData(in_flight_meta_bytes).as_dict())

                return messages

            elif event == 28 or event == 32:
                self.state = DecoderState.ERROR
                return None

            else:
                self.state = DecoderState.POSTFLIGHT
                return [PostFlightPacket(data_bytes).as_dict()]

        except Exception as e:
            print(e)
            return None


    def modify(self, telemetry: dict) -> dict:
        """
        Modifies a decoded telemetary dict to be acceptable
        to the user interaces. For instance remove NULLs from
        name and format floats to strings
        """
        if telemetry is not None:
            # apply modifiers from our list
            telemetry = self.apply_modifiers(telemetry)

            # add separate event name value:
            try:
                event = telemetry["event"]
                telemetry["eventName"] = f"{self.event_names[event]} [{event}]"
            except:
                pass # if [event] doesn't exist in telemetry then it will give exception, we ignore

            # if there's a cont code (PREFLIGHT) then also add the name for it
            try:
                cont = telemetry["cont"]
                telemetry["contName"] = f"{self.cont_names[cont]} [{cont}]"
            except:
                pass # if [cont] doesn't exist in telemetry then it will give exception, we ignore

            try:
                telemetry = self.format_floats(telemetry)
            except:
                pass

        return telemetry


class SDCardTelemetryDecoder(TelemetryDecoder):
    """
    takes line of FC SD-card data and decodes it into a dictionary:
    """

    TIMESTAMP_RESOLUTION = 1000000 # timestamp least significant figure is 10e-8 seconds
    DEFAULT_ACCEL_RESOLUTION = 1024

    def __init__(self, accel_resolution: int = DEFAULT_ACCEL_RESOLUTION) -> None:
        TelemetryDecoder.__init__(self)

        self.telemetry_keys = None
        # Unique keys found in CSV headers for each flight mode:
        self.unique_keys = { DecoderState.INFLIGHT: "fltEvents",
                             DecoderState.MAXES: "Max Baro Alt",
                             DecoderState.LAUNCH: "launch date",
                             DecoderState.LAND: "landing date",
                             DecoderState.POSTFLIGHT: "Rocket Name" }

        self.accel_resolution = accel_resolution

        self.modifiers = { "time":   self.time_modifier,
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

    def decode(self, line: str) -> dict | None:
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
        if self.state == DecoderState.INFLIGHT and items[0].isnumeric():
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
                if state == DecoderState.INFLIGHT:
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

