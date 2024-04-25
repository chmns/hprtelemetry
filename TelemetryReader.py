from threading import Thread, Event
from time import sleep
import os
import datetime
import time
import queue
import sys
import serial
from time import monotonic
from collections import namedtuple
from TelemetryDecoder import *

SYNC_WORD = bytes.fromhex("A5A5A5A5")
MAX_PACKET_LENGTH = 74
TLM_INTERVAL = 0.2 # 200ms

TLM_EXTENSION = ".tlm"
CSV_EXTENSION = ".csv"

TIME_FORMAT = "%H:%M:%S"

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
        tlm_file = None
        csv_file = None
        csv_saving_state = DecoderState.OFFLINE
        previous_decoder_state = DecoderState.OFFLINE

        # CSV backup file headers (only used if saving to CSV file)
        # we get them ready before running so they can be used quickly later
        inflight_header = self.csv_format(InFlightData.keys + InFlightMetaData.keys)
        postflight_header = self.csv_format(PostFlightPacket.keys)
        preflight_start_position = 0
        postflight_start_position = 0

        preflight_telemetry = {} # to store preflight data for writing when FLIGHT packet comes

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

            # Open binary file for direct data backup
            if tlm_file is None and self.filename is not None: # tlm file isn't open but user has added backup file during running
                try:
                    tlm_file = open(self.filename, 'wb')

                except Exception as error:
                    print(f"Couldn't open file {self.filename}")
                    tlm_file = None
                else:
                    print(f"Open TLM file for writing backup to: {self.filename}")

            # if we have an open TLM file then write the raw data into it
            if tlm_file is not None:
                try:
                    tlm_file.write(telemetry_bytes)
                    tlm_file.flush()
                except Exception as error:
                    print(f"Couldn't write backup data to file {self.filename}\n{str(error)}")

            # Open human-readable CSV file for backup
            if csv_file is None and self.filename is not None: # csv file isn't open but user has added backup file during running
                try:
                    csv_filename = os.path.splitext(self.filename)[0] + CSV_EXTENSION
                    csv_file = open(csv_filename, 'wt')

                except Exception as error:
                    print(f"Couldn't open file {csv_filename}")
                    tlm_file = None
                else:
                    print(f"Open CSV file for writing backup to: {csv_filename}")

            # We still send message to UI even if no telemetry is decoded from packet (maybe is corrupt)
            # So start with empty dict
            received_telemetry = {}
            received_telemetry_messages = []

            try:
                received_telemetry_messages = self.decoder.decode(telemetry_bytes[:-len(SYNC_WORD)])
            except Exception as error:
                print(f"Error decoding data from: {self.serial_port}\n{str(error)}")
                continue

            # INFLIGHT packets actually include 4 telemetry payloads. for now we just merge them
            if received_telemetry_messages is not None:
                for message in received_telemetry_messages:
                    self.messages_decoded += 1
                    # when in flight we just send last of 4 packets to UI to save time updating:
                    received_telemetry |= message # merge telemetry dicts together

            # if there is open csv_file then write
            if csv_file is not None and received_telemetry is not {}:
                """
                CSV files have quite complex behaviour, to try to simulate the CSV file recorded by groundstation
                 - there should only be 1 preflight message (but FC can go PRE->FlIGHT->PRE many times during setup)
                 - i.e. it is possible to go FLIGHT->PREFLIGHT so need to handle this
                 - there should only be 1 postflight message (but we may receive more than this, and dont know which is last)
                 - should not allow POSTFLIGHT->FLIGHT
                 - file should be flushed regularly to ensure it is write to disk
                This code would make better sense as a state machine with transition
                functions, but for now I just use elif cases
                """

                # First take a copy of received telemetry in case we change it for the file
                # (and don't want to send these changes to UI)
                csv_telemetry = received_telemetry.copy()

                # Always add date and time info to PREFLIGHT packets
                if self.decoder.state == DecoderState.PREFLIGHT:
                    csv_telemetry["date"] = datetime.date.today().isoformat()
                    csv_telemetry["time"] = time.strftime(TIME_FORMAT)

                # State transitions
                # -----------------
                # 1. OFFLINE -> PREFLIGHT
                if previous_decoder_state == DecoderState.OFFLINE and \
                   self.decoder.state     == DecoderState.PREFLIGHT:
                    # Set file state to PREFLIGHT
                    csv_saving_state = DecoderState.PREFLIGHT

                    # Record file header (PREFLIGHT keys + date and time)
                    csv_file.write(self.csv_format(csv_telemetry.keys()))

                    # Record position of start of PREFLIGHT packet:
                    preflight_start_position = csv_file.tell()

                # 2. PREFLIGHT -> PREFLIGHT
                elif previous_decoder_state == DecoderState.PREFLIGHT and \
                     self.decoder.state     == DecoderState.PREFLIGHT:
                    # If we have not yet seen any FLIGHT data but already saw PREFLIGHT data...
                    if csv_saving_state == DecoderState.PREFLIGHT:
                        # then we go back to start of PREFLIGHT packet and erase
                        csv_file.seek(preflight_start_position)
                        csv_file.truncate()

                # 3. PREFLIGHT -> INFLIGHT
                elif previous_decoder_state == DecoderState.PREFLIGHT and \
                     self.decoder.state     == DecoderState.INFLIGHT:
                    # if this is the first time we see this transition, move to FLIGHT writer state...
                    if csv_saving_state == DecoderState.PREFLIGHT:
                        # ... set the writer state to FLIGHT and ...
                        csv_saving_state = DecoderState.INFLIGHT
                        # ...write the FLIGHT data headers:
                        csv_file.write(inflight_header)

                # 4. INFLIGHT -> POSTFLIGHT: write postflight header
                elif previous_decoder_state == DecoderState.INFLIGHT and \
                     self.decoder.state     == DecoderState.POSTFLIGHT:

                    if csv_saving_state == DecoderState.INFLIGHT:
                        csv_saving_state = DecoderState.POSTFLIGHT
                        csv_file.write(postflight_header) # write postflight header then...
                        postflight_start_position = csv_file.tell() # store start of postflight data for use later
                        csv_file.flush() # ensure last flight data was written to disk

                # 5. POSTFLIGHT -> POSTFLIGHT: overwrite last postflight message
                elif previous_decoder_state == DecoderState.POSTFLIGHT and \
                     self.decoder.state     == DecoderState.POSTFLIGHT:
                     csv_file.seek(postflight_start_position)
                     csv_file.truncate()

                # Only if we are receiving the packets we expect, write to file:
                if self.decoder.state == csv_saving_state:
                    csv_file.write(self.csv_format(csv_telemetry.values()))

                # Finely store old state
                previous_decoder_state = self.decoder.state

            # add merged dict to queue for UI:
            message_queue.put(Message(self.decoder.modify(received_telemetry), # the telemetry dictionarie modify for UI display
                                      self.decoder.state, # current decoder state (PRE/INFLIGHT/POST)
                                      monotonic(), # current time in float seconds. monotonic() is not affected by time/date/zone changes
                                      self.bytes_received, # total number of bytes receive so far
                                      self.messages_decoded)) # total number of good messages so far


        # after ending serial port reading we must clean up:
        if tlm_file is not None:
            tlm_file.close()

        if csv_file is not None:
            csv_file.close()

        if port is not None:
            port.close()

        running.clear()

    def csv_format(self, values: list):
        return ",".join(map(str,values)) + "\n"


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

    def __init__(self, *kargs) -> None:
        TelemetrySerialReader.__init__(self, *kargs)
        self.decoder = RadioTelemetryDecoder()
        self.read = lambda port: serial.Serial.read_until(port,
                                                          SYNC_WORD,
                                                          MAX_PACKET_LENGTH)


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


class BinaryFileReader(TelemetryReader):
    """
    Class for reading TLM file backup data
    """
    def __init__(self, queue: queue.Queue = None) -> None:

        TelemetryReader.__init__(self, queue)
        self.filename = None
        self.decoder = RadioTelemetryDecoder()

    def __run__(self, message_queue, running) -> None:

        assert self.filename is not None

        print(f"Reading binary (TLM) telemetry file {self.filename}")

        last_timestamp = 0

        try:
            with open(self.filename, 'rb') as file:
                raw_data = file.read()

                if not running.is_set():
                        return

                packets = raw_data.split(SYNC_WORD)

                for packet in packets:
                    if not running.is_set():
                        return

                    try:
                        packet = packet + SYNC_WORD # hack: should not need to add SYNC word here
                        self.bytes_received += len(packet) # keep track of total amount of data we got since start
                        decoded_messages = self.decoder.decode(packet)
                    except Exception as error:
                        print(f"Error decoding data\n{str(error)}")

                    if decoded_messages is not None:
                        for message in decoded_messages:
                            self.messages_decoded += 1
                            message_queue.put(Message(message,
                                              self.decoder.state,
                                              monotonic(),
                                              self.bytes_received,
                                              self.messages_decoded))

                    sleep(TLM_INTERVAL)

        except IOError:
            print(f"Cannot read file: {self.filename}")

        finally:
            running.clear()

        print(f"Finished reading TLM file {self.filename}")
