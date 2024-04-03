
from TelemetryDecoder import TelemetrySerialReader
import queue
import serial
import struct

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
            "rocketName",  # char[20?] rocketName
            "base_alt",    # uint16_t  baseAlt
            "gps_alt",     # uint16_t  GPSalt
            "gps_lat",     # float     GPS.location.lat
            "gps_lon",     # float     GPS.location.lng
            "num_sats",    # uint16_t  satNum
            "callsign"]    # char[6]   callsign

    format = "@BBB20sHHffH20s"

class FlightData:
    keys = ["event",    # uint8_t event
            "fltTime",  # int16_t fltTime
            "vel",      # int16_t vel
            "alt",      # int16_t alt
            "roll",     # int16_t roll
            "off_vert", # int16_t offVert
            "accel"]    # int16_t accel

    format = "@B6H"

class InFlightPacket(RadioPacket):
    """
    4x
        FlightData (13 bytes)
    1x
        int16_t packetnum
        int16_t GPSalt
        float   GPS.location.lat
        float   GPS.location.lon
        char[6] callsign
    """

    format = "@13B13B13B13BHHff6s"

    def __init__(self, data_bytes):
        (self.flight_data_1,
         self.flight_data_2,
         self.flight_data_3,
         self.flight_data_4,
         self.packetnum,
         self.gps_alt,
         self.gps_lat,
         self.gps_lon,
         self.callsign) = struct.unpack(self.format, data_bytes)


class PostFlightPacket(RadioPacket):
    keys = ["event",        # uint8_t  event
            "max_alt",      # uint16_t maxAlt
            "max_vel",      # uint16_t maxVel
            "max_g",        # uint16_t maxG
            "max_gps_alt",  # uint16_t maxGPSalt
            "gps_fix",      # uint8_t  gnss.fix
            "gps_alt",      # uint16_t GPSalt
            "gps_lat",      # float    GPS.location.lat
            "gps_lon",      # float    GPS.location.lng
            "callsign"]     # char[6]  callsign

    format = "@B4HBHff6s"



class RadioTelemetryDecoder(object):
    """
    Converts flight telemetry received over radio direct from vehicle
    into SD-card style data for sending to UI (which is wanting SD-card style)
    """

    event_names =  ["Preflight",
                    "Liftoff",
                    "Booster Burnout",
                    "Apogee Detected",
                    "Firing Apogee Pyro",
                    "Separation Detected",
                    "Firing Mains",
                    "Under Chute",
                    "Ejecting Booster",
                    "Firing 2nd Stage",
                    "2nd Stage Ignition",
                    "2nd Stage Burnout",
                    "Firing Airstart1",
                    "Airstart 1 Ignition",
                    "Airstart 1 Burnout",
                    "Firing Airstart2",
                    "Airstart 2 Ignition",
                    "Airstart 2 Burnout",
                    "NoFire: Rotn Limit",
                    "NoFire: Alt Limit",
                    "NoFire: Rotn/Alt Lmt",
                    "Booster Apogee",
                    "Booster Apogee Fire",
                    "Booster Separation",
                    "Booster Main Deploy",
                    "Booster Under Chute",
                    "Time Limit Exceeded",
                    "Touchdown!",
                    "Power Loss! Restart",
                    "Booster Touchdown",
                    "Booster Preflight",
                    "Booster Time Limit",
                    "Booster Pwr Restart"]

    def __init__(self) -> None:
        pass

    def decode(self, data_bytes) -> dict | None:

        event = data_bytes[0]

        try:
            if event == 0 or event == 30:
                return dict(PreFlightPacket(data_bytes))
            elif event < 26:
                return dict(InFlightPacket(data_bytes))
            else:
                return dict(PostFlightPacket(data_bytes))

        except Exception:
            return None


class RadioTelemetryReader(TelemetrySerialReader):
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

        return data_bytes
