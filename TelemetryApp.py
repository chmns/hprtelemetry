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

TEST_DATA_FILENAME = "FLIGHT10-short.csv"

UPDATE_DELAY = 100

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
- quit threads correctly on close window

- connect:
-- pre and post GNSS locations
-- map add markers to make trace
-- multipliers (raw accel -> m/s)
-- secondary units (m/s -> kmh etc)

- update graphs at different rate to rest of UI

- listen to serial port
-- select serial port
-- decode CRC32

- menus and buttons:
-- reset
-- connect to serial port

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
                               "gnssSpeed", "gnssAlt", "gnssAngle", "gnssSatellites", "radioPacketNum"]

        for var in self.telemetry_vars:
            self.setvar(var)

        self.running = BooleanVar(self, False, "running")

        self.serial_reader = TelemetrySerialReader(self.message_queue)
        self.file_reader = TelemetryFileReader(self.message_queue)

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

        current_serial = StringVar(self, name="current_serial", value=None)

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

        self.altitude_graph = GraphFrame(self, "m", ALTITUDE_COLOR, None, "time", "accelX", "accelY", "accelZ")
        self.altitude_graph.grid(row=0, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.altitude_graph.grid_propagate(True)

        self.velocity_graph = GraphFrame(self, "m/s", VELOCITY_COLOR, None, "time", "intVel", "fusionVel", "gnssSpeed")
        self.velocity_graph.grid(row=1, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.velocity_graph.grid_propagate(True)

        self.acceleration_graph = GraphFrame(self, "m/s/s", ACCELERATION_COLOR, (-20.0, 80.0), "time", "highGx", "highGy", "highGz", "smoothHighGz")
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

        self.controls = TelemetryControls(self)
        self.controls.grid(row=2, column=6, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.controls.config(width = CELL_WIDTH)
        self.controls.grid_propagate(False)

        self.bind('q', lambda _: self.quit())
        self.bind('s', lambda _: print(self.serial_reader.available_ports()))
        self.bind('r', lambda _: self.reset())
        self.focus()

        def on_closing():
            self.destroy()
            self.quit()

        self.protocol("WM_DELETE_WINDOW", on_closing)

    def update(self):
        self.running.set(True)

        try:
            while True:
                self.message_callback(self.message_queue.get(block=False))
        except queue.Empty:
            return
        finally:
            if self.file_reader.running.is_set() or \
            self.serial_reader.running.is_set():
                self.after(UPDATE_DELAY, self.update)
            else:
                self.running.set(False)

    def message_callback(self, message, state = None):
        """
        decodes FC-style message into app variables and triggers graphs + map to update
        """
        if isinstance(message, dict):
            for (key, value) in message.items():
                self.setvar(key, value)

        if self.state == DecoderState.FLIGHT:
            self.map_frame.update()
            # self.altitude_graph.append(self.altitude.variable.get())


    def reset(self) -> None:
        """
        resets the app back to zero
        for when loading new file or connecting to new serial port
        """
        # stop file decoder if it's running
        # stop serial decoder if it's running
        self.file_reader.stop()
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

        ports = self.serial_reader.ports()

        if len(ports) == 0:
            self.serial_menu.add_command("No serial ports", state=DISABLED)
        else:
            for port in ports:
                self.serial_menu.add_command(label=port, command=print)

        self.serial_menu.add_separator()
        self.serial_menu.add_command(label="Re-scan", command=self.update_serial_menu)

        self.menubar.add_cascade(label="Serial Port", menu=self.serial_menu)


    def open_telemetry_file(self):
        filename = askopenfilename(filetypes =[('Telemetry Text Files', '*.csv'), ('Other Telemetry Files', '*.*')])
        print(f"Attempting to open file {filename}")
        if filename is not None:
            self.file_reader.filename = filename
            self.file_reader.start()
            self.update()


if __name__ == "__main__":
    telemetry = TelemetryApp()
    telemetry.mainloop()
    telemetry.quit()

