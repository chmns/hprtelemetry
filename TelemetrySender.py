from TelemetryReader import TelemetryReader
from TelemetryDecoder import PreFlightPacket, InFlightData, InFlightMetaData, PostFlightPacket
import struct
from time import sleep
import serial
from zlib import crc32

CALLSIGN = "QQ0523".encode("ascii")
NAME = "Test Flight Rocket 1".encode("ascii")
SYNC_WORD = bytes.fromhex("A5A5A5A5")

class TelemetryTestSender(TelemetryReader):

    TEST_MESSAGE_INTERVAL = 0.05

    def __init__(self) -> None:

        self.filename = None
        self.serial_port = "COM3"
        TelemetryReader.__init__(self, None)

        flight_packet = bytearray(struct.pack(InFlightData.format, 1, 500, 200, 300, 1200, 2200, 505))
        flight_packet += struct.pack(InFlightMetaData.format, 10, 220, 45.79160, 0.59950, CALLSIGN)

        self.test_packets = [
            #                                   Event   Fix    Cont  Name   Baro    gAlt    gLat        gLon        sats    call
            struct.pack(PreFlightPacket.format, 0,      False, 0,    NAME,  100,    200,    45.79164,   0.59958,    0,      CALLSIGN),
            struct.pack(PreFlightPacket.format, 0,      True,  1,    NAME,  110,    210,    45.79165,   0.59957,    1,      CALLSIGN),
            struct.pack(PreFlightPacket.format, 0,      True,  2,    NAME,  120,    220,    45.79166,   0.59956,    3,      CALLSIGN),

            flight_packet,
            #                                    Event  mAlt,   mVel,   mG, mGAlt,
            struct.pack(PostFlightPacket.format, 26, 100,  200, 3, 1000, True, 1001, 45.79166, 0.59956, CALLSIGN),
        ]

    def send_single_packet(self, packet_number: int):
        assert self.serial_port is not None
        port = None

        if packet_number < 0 or packet_number >= len(self.test_packets):
            return

        try:
            port = serial.Serial(port=self.serial_port,
                                 baudrate=57600,
                                 timeout=1)
        except:
            print(f"Test sender could not open serial port: {self.serial_port}")
            return

        try:
            # print(f"Sending packet {packet} out of port: {self.serial_port}")
            packet = self.test_packets[packet_number]

            port.write(packet)
            port.write(int.to_bytes(crc32(packet),4))
            port.write(SYNC_WORD)
            # for packet in self.test_packets:
                # port.write(packet)
                # port.write(SYNC_WORD)

        except IOError as e:
            print(e)
        finally:
            port.close()

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
