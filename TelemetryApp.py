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
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox
from TelemetryDecoder import *
from matplotlib import style
import queue
from pathlib import Path
style.use('dark_background')

UPDATE_DELAY = 100 # ms between frames

NUM_COLS = 7
NUM_ROWS = 3
PADX = 4
PADY = 4

SASH_WIDTH = 10

ALTITUDE_COLOR = "#8BD3E6"
VELOCITY_COLOR = "#FF6D6A"
ACCELERATION_COLOR = "#EFBE7D"
LIGHT_GRAY = "#AAAAAA"
DARK_RED = "#AA3333"
DARK_GREEN = "#33AA33"
WHITE = "#EEEEEE"

DEFAULT_COORD = "0.0000000"
PREFLIGHT_COORDS_PREFIX = "Pre: "
CURRENT_COORDS_PREFIX = "Curr:"
POSTFLIGHT_COORDS_PREFIX = "Post:"

CELL_WIDTH = 220

"""
todo:

x.  add preflight state decoding
x.  add postflight state decoding
x.  fix file reading delay
x.  low-speed map updating with markers
5.  status display (listening to port, reading file etc)
x.  graph rendering
7.  secondary units (m/s -> kmh etc)
x.  prompt to write out to file when listening to serial port
x.  offline maps
10. final value display (in addition to rolling max/min)
11. add online/offline toggle to map itself
12. add download current area to map itself

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

        self.telemetry_vars = ["name",
                               "time", "accelX", "accelY", "accelZ", "gyroZ" "highGx", "highGy", "highGz",
                               "smoothHighGz", "offVert", "intVel", "intAlt", "fusionVel", "fusionAlt",
                               "fltEvents", "radioCode", "baroAlt", "altMoveAvg", "gnssLat", "gnssLon",
                               "landing_latitude", "landing_longitude", "landing_time",
                               "launch_latitude", "launch_longitude", "launch_time",
                               "gnssSpeed", "gnssAlt", "gnssAngle", "gnssSatellites", "radioPacketNum"]

        """
        priority variables are always updated when a new message comes in
        (vars not in this list overwrite the last known value and only update at
        the selected frame rate)
        """
        self.priority_vars = ["time", "name", "accelZ", "functionAlt", "fusionVel"]

        for var in self.telemetry_vars:
            self.setvar(var)

        self.running = BooleanVar(self, False, "running")

        self.serial_reader = TelemetrySerialReader(self.message_queue)
        self.serial_reader.name = "serial_reader"
        self.file_reader = TelemetryFileReader(self.message_queue)
        self.file_reader.name = "file_reader"

        # for testing only:
        self.test_serial_sender = TelemetryTestSender()

        self.title("HPR Telemetry Viewer")
        self.config(background="green")
        # self.config(background="#222222")

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (w, h))

        # create a menubar
        self.menubar = Menu(self)
        self.config(menu=self.menubar)

        self.file_menu = Menu(self.menubar)
        self.file_menu.add_command(label="Open", command=self.open_telemetry_file)
        self.file_menu.add_command(label="Reset", command=self.reset)
        self.file_menu.add_command(label='Exit', command=self.destroy)

        self.map_menu = Menu(self.menubar)
        self.map_menu.add_command(label="Download current map", command=self.download_current_map)
        self.map_menu.add_command(label="Set offline map path", command=self.set_offline_path)
        self.offline_maps_only = BooleanVar(self, True, "offline_maps_only")

        self.map_menu.add_checkbutton(label="Only use offline maps",
                                      command=self.toggle_offline_maps_only,
                                      variable=self.offline_maps_only)

        self.serial_menu = Menu(self.menubar)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.menubar.add_cascade(label="Serial", menu=self.serial_menu)
        self.menubar.add_cascade(label="Map", menu=self.map_menu)

        self.update_serial_menu()

        self.window = PanedWindow(orient="horizontal", background="#aaaaaa")
        self.window.configure(sashwidth=SASH_WIDTH)
        self.readouts = Frame(self.window, width=CELL_WIDTH*2, background=BG_COLOR)
        self.graphs = Frame(self.window, width=400, background="black")
        self.map_column = PanedWindow(self.window, orient="vertical", background="black")

        self.window.add(self.readouts)
        self.window.add(self.graphs, stretch="always")
        self.window.add(self.map_column)

        self.window.pack(fill="both", expand=True)

        self.window.sash_place(0, CELL_WIDTH, 0)
        self.window.sash_place(1, CELL_WIDTH, 0)

        self.altitude = ReadOut(self.readouts, "Altitude", "fusionAlt", "m", "ft", ReadOut.metresToFeet, ALTITUDE_COLOR)
        self.altitude.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=(N,E,W,S))
        self.altitude.config(width = CELL_WIDTH)

        self.velocity = ReadOut(self.readouts, "Velocity", "fusionVel", "m/s", "mi/h", ReadOut.msToMph, VELOCITY_COLOR)
        self.velocity.grid(row=1, column=0, padx=PADX, pady=PADY, sticky=(N,S))
        self.velocity.config(width = CELL_WIDTH)

        self.acceleration = ReadOut(self.readouts, "Accel", "accelZ", "m/s/s", "G", ReadOut.mssToG, ACCELERATION_COLOR)
        self.acceleration.grid(row=2, column=0, padx=PADX, pady=PADY, sticky=(N,S))
        self.acceleration.config(width = CELL_WIDTH)

        self.readouts.columnconfigure(0, weight=1)
        for i in range (NUM_ROWS):
            self.readouts.rowconfigure(i, weight=1)

        self.altitude_graph = GraphFrame(self.graphs,
                                         "m",
                                         DoubleVar(self, 0.0, "time"),
                                         DoubleVar(self, 0.0, "fusionAlt"),
                                         None,
                                         ALTITUDE_COLOR)
        self.altitude_graph.grid(row=0, column=0, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))

        self.velocity_graph = GraphFrame(self.graphs,
                                         "m/s",
                                         DoubleVar(self, 0.0, "time"),
                                         DoubleVar(self, 0.0, "fusionVel"),
                                         None,
                                         VELOCITY_COLOR)
        self.velocity_graph.grid(row=1, column=0, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))

        self.acceleration_graph = GraphFrame(self.graphs,
                                             "m/s/s",
                                             DoubleVar(self, 0.0, "time"),
                                             DoubleVar(self, 0.0, "accelZ"),
                                             (-20.0, 80.0),
                                             ACCELERATION_COLOR)
        self.acceleration_graph.grid(row=2, column=0, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.graphs.columnconfigure(0, weight=1)

        for i in range (NUM_ROWS):
            self.graphs.rowconfigure(i, weight=1)


        self.map_frame = MapFrame(self.map_column,
                                  DoubleVar(self, 0.0, "gnssLat"),
                                  DoubleVar(self, 0.0, "gnssLon"),
                                  DoubleVar(self, 0.0, "gnssAlt"),
                                  self.offline_maps_only)
        self.map_frame.grid(row=0, column=0, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))

        self.tilt_spin = TiltAndSpin(self.map_column, "offVert", "gyroZ")
        self.tilt_spin.grid(row=1, column=0, padx=PADX, pady=PADY, sticky=(N,E,S,W))

        self.status = TelemetryStatus(self.map_column, "name", "radioPacketNum", "time", "gnssSatellites")
        self.status.grid(row=1, column=1, padx=PADX, pady=PADY, sticky=(N,E,S,W))

        self.controls = TelemetryControls(self.map_column, self.serial_reader)
        self.controls.grid(row=1, column=2, padx=PADX, pady=PADY, sticky=(N,E,S,W))

        self.status_bar = Frame(self.map_column, background=BG_COLOR)
        self.status_bar.grid(row=2, column=0, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.status_label = Label(self.status_bar, font="Arial 24", text="Disconnected", bg=BG_COLOR, fg=LIGHT_GRAY, anchor=E, justify="left")
        self.status_label.pack(fill=BOTH)

        self.map_column.rowconfigure(0, weight=2)
        self.map_column.rowconfigure(1, weight=1)

        for i in range (3):
            self.map_column.columnconfigure(i, weight=1)


        self.download_overlay = None

        self.bind('q', lambda _: self.quit())
        self.bind('s', lambda _: print(self.serial_reader.available_ports()))
        self.bind('r', lambda _: self.reset())
        self.bind('t', lambda _: self.open_telemetry_test_file())
        self.focus()

        self.offline_map_path = str(Path.home() / "Documents")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def set_status_text(self, text,
                        color:str = None,
                        bg: str = None):
        print(f"{text=}, {color=}, {bg=}")
        self.status_label.config(text=text)

        if color is not None:
            self.status_label.config(fg=color)

        if bg is not None:
            self.status_label.config(bg=bg)
        else:
            self.status_label.config(bg=BG_COLOR)

    def on_closing(self):
        self.test_serial_sender.stop()
        self.serial_reader.stop()
        self.file_reader.stop()
        self.destroy()
        self.quit()

    def update(self):
        self.running.set(True)

        telemetry_buffer = {}
        current_state = None
        counter = 0

        try:
            while True:
                message = self.message_queue.get(block=False)

                if message is not None:
                    (telemetry, state) = message

                    # it state changed (launch -> flight, flight -> landed etc)
                    # then we must decode whole message
                    if current_state is not state:
                        self.message_callback(message)
                        current_state = state
                        counter = 0

                    # else we just collate the new telemetry values and update the
                    # most important ones:
                    else:
                        self.priority_message_callback(message)
                        # combine dicts, updating with new values
                        telemetry_buffer = telemetry_buffer | telemetry

                        counter += 1

        except queue.Empty:
            if telemetry_buffer is not {}:
                self.message_callback((telemetry_buffer, current_state))

        finally:
            if self.file_reader.running.is_set() or self.serial_reader.running.is_set():
                self.after(UPDATE_DELAY, self.update)
            else:
                print("Finished reading")

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
                self.setvar("launch_time", telemetry["UTC_time"])
                self.map_frame.set_launch_point(float(self.getvar("launch_latitude")),
                                                float(self.getvar("launch_longitude")))
            case DecoderState.LAND:
                self.setvar("landing_time", telemetry["UTC_time"])
                self.map_frame.set_landing_point(float(self.getvar("landing_latitude")),
                                                 float(self.getvar("landing_longitude")))


    def stop(self) -> None:
        """
        stops recording and/or playing back serial or file
        but does not reset the graphs and map e.t.c.
        """
        # stop file decoder if it's running
        self.file_reader.stop()
        # stop serial decoder if it's running
        self.serial_reader.stop()
        self.set_status_text("Disconnected", LIGHT_GRAY)

    def reset(self) -> None:
        """
        resets the app back to zero and stops recording or playback
        for when loading new file or connecting to new serial port
        """
        self.stop()
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

        self.serial_menu.add_command(label="Disconnect", command=self.stop)

        ports = self.serial_reader.available_ports()

        if len(ports) == 0:
            self.serial_menu.add_command("No serial ports", state=DISABLED)
        else:
            for port in ports:
                self.serial_menu.add_command(label=port, command=lambda: self.listen_to_port(port))

        self.serial_menu.add_separator()
        self.serial_menu.add_command(label="Re-scan", command=self.update_serial_menu)

    def listen_to_port(self, port):
        print(f"Attempting to listen to {port}")
        if port in self.serial_reader.available_ports():
            yesnocancel = messagebox.askyesnocancel(f"Listen on serial port {port}",
                                                    "Do you want to save a backup of this telemetry to disk?")

            if yesnocancel is None:
                return

            self.reset()

            if yesnocancel:
                filename = asksaveasfilename(filetypes =[('Telemetry Text Files', '*.csv')])
                print(f"Saving telemetry from serial port {port} to file {filename}")
                self.serial_reader.filename = filename
                self.set_status_text(f"Recording serial port {port}", WHITE, DARK_RED)
            else:
                print(f"Not saving telemetry from serial port {port} to file")
                self.set_status_text(f"Listening serial port {port} (Not Recording)", WHITE)

            self.serial_reader.serial_port = port
            self.serial_reader.start()
            self.update()

    def open_telemetry_file(self):
        filename = askopenfilename(filetypes =[('Telemetry Text Files', '*.csv'), ('Other Telemetry Files', '*.*')])
        if filename != "":
            self.reset()
            self.file_reader.filename = filename
            self.set_status_text(f"Playing: {filename}", WHITE, DARK_GREEN)
            self.file_reader.start()
            self.update()

    def open_telemetry_test_file(self):
        filename = askopenfilename(filetypes =[('Telemetry Text Files', '*.csv'), ('Other Telemetry Files', '*.*')])
        if filename != "":
            self.test_serial_sender.stop()
            self.test_serial_sender.serial_port = "COM3"
            self.test_serial_sender.filename = filename
            self.test_serial_sender.start()

    def download_current_map(self):

        try:
            self.download_overlay = Frame(self, background="#0f0f0f")
            self.download_overlay.grid(row=0, column=0, rowspan=3, columnspan=7, sticky=(N,E,S,W))

            ok = messagebox.askokcancel("Download current map",
                                        "This will currently displayed location at all zoom levels. Depending on internet connection this require take several minutes.\n\nDuring download the app will be unresponsive.\n\nAre you sure you wish to continue?")

            if not ok:
                return

            self.map_frame.download_current_map()

        except Exception:
            messagebox.showerror("Downloading Error",
                                 "Unable to download map, check internet connection")
            return

        else:
            messagebox.showinfo("Downloading Successful",
                                f"Saved current location to database: {self.map_frame.database_path}")

        finally:
            self.download_overlay.destroy()
            self.download_overlay = None


    def set_offline_path(self):
        filename = askopenfilename(filetypes =[('Map Database', '*.db'), ('Other Files', '*.*')])
        if filename is not None:
            print(f"Attempting to load map file: {filename}")
            self.map_frame.load_offline_database(filename)
        pass

    def toggle_offline_maps_only(self):
        offline_maps_only = self.offline_maps_only.get()
        self.map_frame.set_only_offline_maps(offline_maps_only)



if __name__ == "__main__":
    telemetry = TelemetryApp()
    telemetry.mainloop()
    telemetry.quit()

