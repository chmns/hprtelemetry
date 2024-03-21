"""
Telemetry viewer for HPR flight computer by SparkyVT

This will accept radio packet data and display on a laptop or PC
either from COM port (RFD900 with FDTI) ou Teensy USB output (to do...)

Start: 6e Dec 2023
MFL
"""

from tkinter import *
from GraphFrame import GraphFrame
from TelemetryControls import *
from MapFrame import *
from tkinter.filedialog import askopenfilename
from TelemetryDecoder import *
from matplotlib import style
import queue
style.use('dark_background')

UPDATE_DELAY = 100 # ms between frames

NUM_COLS = 7
NUM_ROWS = 3
PADX = 4
PADY = 4

ALTITUDE_COLOR = "#8BD3E6"
VELOCITY_COLOR = "#FF6D6A"
ACCELERATION_COLOR = "#EFBE7D"

DEFAULT_COORD = "0.0000000"
PREFLIGHT_COORDS_PREFIX = "Pre: "
CURRENT_COORDS_PREFIX = "Curr:"
POSTFLIGHT_COORDS_PREFIX = "Post:"

CELL_WIDTH = 280

"""
todo:

x. add preflight state decoding
x. add postflight state decoding
x. fix file reading delay
4. low-speed map updating with markers
5. status display (listening to port, reading file etc)
6. graph rendering
7. secondary units (m/s -> kmh etc)
8. prompt to write out to file when listening to serial port

"""

class TelemetryApp(Tk):

    def __init__(self,
                 screenName: str | None = None,
                 baseName: str | None = None,
                 className: str = "Tk",
                 useTk: bool = True,
                 sync: bool = False,
                 use: str | None = None) -> None:

        super().__init__(screenName, baseName, className, useTk, sync, use)

        self.message_queue = queue.Queue()
        self.running = TRUE

        self.telemetry_vars = ["time", "accelX", "accelY", "accelZ", "gyroZ" "highGx", "highGy", "highGz",
                               "smoothHighGz", "offVert", "intVel", "intAlt", "fusionVel", "fusionAlt",
                               "fltEvents", "radioCode", "baroAlt", "altMoveAvg", "gnssLat", "gnssLon",
                               "landing_latitude", "landing_longitude", "landing_time",
                               "launch_latitude", "launch_longitude", "launch_time",
                               "gnssSpeed", "gnssAlt", "gnssAngle", "gnssSatellites", "radioPacketNum"]

        self.priority_vars = ["time", "name", "accelZ", "functionAlt", "fusionVel"]

        for var in self.telemetry_vars:
            self.setvar(var)

        self.running = BooleanVar(self, False, "running")

        self.serial_reader = TelemetrySerialReader(self.message_queue)
        self.file_reader = TelemetryFileReader(self.message_queue)

        # for testing only:
        self.test_serial_sender = TelemetryTestSender()

        self.title("HPR Telemetry Viewer")
        self.config(background="#222222")

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (w, h))

        # create a menubar
        self.menubar = Menu(self)
        self.config(menu=self.menubar)

        self.file_menu = Menu(self.menubar)
        self.file_menu.add_command(label="Open", command=self.open_telemetry_file)
        self.file_menu.add_command(label="Reset", command=self.reset)
        self.file_menu.add_command(label='Exit', command=self.destroy)

        self.serial_menu = Menu(self.menubar)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.menubar.add_cascade(label="Serial", menu=self.serial_menu)

        self.update_serial_menu()

        current_serial_port = StringVar(self, name="current_serial", value=None)

        # fixed column widths
        for col in range (NUM_COLS):
            self.columnconfigure(col, weight=0)

        # single column expands with width:
        self.columnconfigure(1, weight=1)

        # fixed row heights
        for row in range(NUM_ROWS):
            self.rowconfigure(row, weight=1)

        self.altitude = ReadOut(self, "Altitude", "fusionAlt", "m", "ft", ReadOut.metresToFeet, ALTITUDE_COLOR)
        self.altitude.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=(N,S))
        self.altitude.config(width = CELL_WIDTH)
        self.altitude.grid_propagate(False)

        self.velocity = ReadOut(self, "Velocity", "fusionVel", "m/s", "mi/h", ReadOut.msToMph, VELOCITY_COLOR)
        self.velocity.grid(row=1, column=0, padx=PADX, pady=PADY, sticky=(N,S))
        self.velocity.config(width = CELL_WIDTH)
        self.velocity.grid_propagate(False)

        self.acceleration = ReadOut(self, "Acceleration", "accelZ", "m/s/s", "G", ReadOut.mssToG, ACCELERATION_COLOR)
        self.acceleration.grid(row=2, column=0, padx=PADX, pady=PADY, sticky=(N,S))
        self.acceleration.config(width = CELL_WIDTH)
        self.acceleration.grid_propagate(False)

        self.altitude_graph = GraphFrame(self,
                                         "m",
                                         DoubleVar(self, 0.0, "time"),
                                         DoubleVar(self, 0.0, "fusionAlt"),
                                         None,
                                         ALTITUDE_COLOR)
        self.altitude_graph.grid(row=0, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.altitude_graph.grid_propagate(True)

        self.velocity_graph = GraphFrame(self,
                                         "m/s",
                                         DoubleVar(self, 0.0, "time"),
                                         DoubleVar(self, 0.0, "fusionVel"),
                                         None,
                                         VELOCITY_COLOR)
        self.velocity_graph.grid(row=1, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.velocity_graph.grid_propagate(True)

        self.acceleration_graph = GraphFrame(self,
                                             "m/s/s",
                                             DoubleVar(self, 0.0, "time"),
                                             DoubleVar(self, 0.0, "accelZ"),
                                             (-20.0, 80.0),
                                             ACCELERATION_COLOR)
        self.acceleration_graph.grid(row=2, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.acceleration_graph.grid_propagate(True)

        self.map_frame = MapFrame(self, "gnssLat", "gnssLon", "gnssAlt")
        self.map_frame.grid(row=0, column=4, rowspan=2, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.map_frame.grid_propagate(False)

        self.tilt_spin = TiltAndSpin(self, "offVert", "gyroZ")
        self.tilt_spin.grid(row=2, column=4, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.tilt_spin.config(width = CELL_WIDTH)
        self.tilt_spin.grid_propagate(False)

        self.status = TelemetryStatus(self, "name", "radioPacketNum", "time", "gnssSatellites")
        self.status.grid(row=2, column=5, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.status.config(width = CELL_WIDTH)
        self.status.grid_propagate(False)

        self.controls = TelemetryControls(self, self.serial_reader)
        self.controls.grid(row=2, column=6, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.controls.config(width = CELL_WIDTH)
        self.controls.grid_propagate(False)

        self.bind('q', lambda _: self.quit())
        self.bind('s', lambda _: print(self.serial_reader.available_ports()))
        self.bind('r', lambda _: self.reset())
        self.bind('t', lambda _: self.open_telemetry_test_file())
        self.focus()

        def on_closing():
            print("stopping test_serial_sender")
            self.test_serial_sender.stop()
            print("stopping serial_reader")
            self.serial_reader.stop()
            print("stopping file_reader")
            self.file_reader.stop()
            self.destroy()
            self.quit()

        self.protocol("WM_DELETE_WINDOW", on_closing)

    def update(self):
        self.running.set(True)

        message = None

        try:
            while True: # need to take in account the Decoder State here,
                        # as non-flight messages only have single line which gets lost
                message = self.message_queue.get(block=False)
                self.priority_message_callback(message)

        except queue.Empty:
            if message is not None:
                self.message_callback(message)

        finally:
            self.after(UPDATE_DELAY, self.update)

    def priority_message_callback(self, message):
        (telemetry, state) = message

        if isinstance(telemetry, dict):
            for priority_var in self.priority_vars:
                if priority_var in telemetry.keys():
                    self.setvar(priority_var, telemetry[priority_var])

                self.altitude_graph.update()
                self.acceleration_graph.update()
                self.velocity_graph.update()

    def message_callback(self, message):
        """
        decodes FC-style message into app variables and triggers graphs + map to update

        todo: instead of reading all variables every time, only read the latest value
              (except for graphed data that should be loaded in bulk across to graphs)
        """
        (telemetry, state) = message

        if isinstance(telemetry, dict):
            for (key, value) in telemetry.items():
                self.setvar(key, value)

                # horrible hack to fix that the name is coming as its own message
                # in FLIGHT DecoderState
                # todo: replace this
                if key == "name":
                    return

        match state:
            case DecoderState.FLIGHT:
                self.map_frame.update()
                self.altitude_graph.render()
                self.acceleration_graph.render()
                self.velocity_graph.render()
            case DecoderState.LAUNCH:
                print("Decoding LAUNCH state")
                self.setvar("launch_time", telemetry["UTC_time"])
                self.map_frame.set_launch_point(float(self.getvar("launch_latitude")),
                                                float(self.getvar("launch_longitude")))
            case DecoderState.LAND:
                print("Decoding LAND state")
                self.setvar("landing_time", telemetry["UTC_time"])
                self.map_frame.set_landing_point(float(self.getvar("landing_latitude")),
                                                 float(self.getvar("landing_longitude")))



    def reset(self) -> None:
        """
        resets the app back to zero
        for when loading new file or connecting to new serial port
        """
        # stop file decoder if it's running
        self.file_reader.stop()
        # stop serial decoder if it's running
        self.serial_reader.stop()

        # clear all telemetry variables:
        for var in self.telemetry_vars:
            self.setvar(var, "0")

        # clear app variables and graphs:
        self.setvar("name", "")
        self.map_frame.reset()
        self.altitude_graph.reset()
        self.velocity_graph.reset()
        self.acceleration_graph.reset()


    def update_serial_menu(self) -> None:
        """
        scans for serial ports and updates menu to show detected ports
        """
        self.serial_menu.delete(0, END)

        ports = self.serial_reader.available_ports()

        if len(ports) == 0:
            self.serial_menu.add_command("No serial ports", state=DISABLED)
        else:
            for port in ports:
                self.serial_menu.add_command(label=port, command=lambda: self.listen_to_port(port))

        self.serial_menu.add_separator()
        self.serial_menu.add_command(label="Re-scan", command=self.update_serial_menu)

        # self.menubar.add_cascade(label="Serial", menu=self.serial_menu)

    def listen_to_port(self, port):
        print(f"Attempting to listen to {port}")
        if port in self.serial_reader.available_ports():
            self.reset()
            self.serial_reader.serial_port = port
            self.serial_reader.start()
            self.update()

    def open_telemetry_file(self):
        filename = askopenfilename(filetypes =[('Telemetry Text Files', '*.csv'), ('Other Telemetry Files', '*.*')])
        if filename is not None:
            self.reset()
            self.file_reader.stop()
            self.file_reader.filename = filename
            self.file_reader.start()
            self.update()

    def open_telemetry_test_file(self):
        filename = askopenfilename(filetypes =[('Telemetry Text Files', '*.csv'), ('Other Telemetry Files', '*.*')])
        if filename is not None:
            self.test_serial_sender.stop()
            self.test_serial_sender.serial_port = "COM3"
            self.test_serial_sender.filename = filename
            self.test_serial_sender.start()


if __name__ == "__main__":
    telemetry = TelemetryApp()
    telemetry.mainloop()
    telemetry.quit()

