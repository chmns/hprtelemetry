import csv
import os
from threading import Thread
from time import sleep


class TestTelemetry(Thread):

    def __init__(self,
                 prelaunch_callback: callable = None,
                 message_callback: callable = None) -> None:
        super().__init__()
        self.prelaunch_callback = prelaunch_callback
        self.message_callback = message_callback

    @staticmethod
    def decodeMessage(message) -> (dict | None):
        try:
            message_dict = {
                "event": message[0],
                "time": float(message[1]),
                "acceleration": float(message[2]),
                "velocity": float(message[3]),
                "altitude": float(message[4]),
                "spin": float(message[5]),
                "tilt": float(message[6]),
                "gpsAlt": float(message[7]),
                "gpsLat": float(message[8]),
                "gpsLon": float(message[9]),
                "signalStrength": float(message[10]),
                "packetNum": message[11]
            }
        except:
            return None
        return message_dict

    @staticmethod
    def decodePrelaunch(message) -> (dict | None):
        print(message)
        try:
            prelaunch_dict = {
                "RocketName": message[1],
                "Continuity": int(message[2]),
                "GPSlock": bool(message[3]),
                "BaseAlt": float(message[4]),
                "GPSalt": float(message[5]),
                "Latitude": float(message[6]),
                "Longitude": float(message[7]),
            }
        except:
            return None
        return prelaunch_dict

    def run(self):
        pwd = os.path.dirname(__file__)
        rel_path = "telemetry/test.txt"
        abs_file_path = os.path.join(pwd, rel_path)

        with open(abs_file_path, 'rt') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', )

            for row in csv_reader:
                if not row[0] == "Telemetry Rocket Recorder":
                    print("Invalid telemetry file")
                    return
                else:
                    break

            for row in csv_reader:
                self.prelaunch_callback(TestTelemetry.decodePrelaunch(row))
                break

            for row in csv_reader:
                if row[0].isnumeric() and self.message_callback is not None:
                    if int(row[0]) > 0 and int(row[0]) < 8:
                        self.message_callback(TestTelemetry.decodeMessage(row))
                        sleep(0.05)
                    

if __name__ == "__main__":
    test = TestTelemetry(print)
    test.start()