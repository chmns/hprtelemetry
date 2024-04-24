"""
Telemetry viewer for HPR flight computer by SparkyVT

This will accept radio packet data and display on a laptop or PC
either from COM port (RFD900 with FDTI) ou Teensy USB output (to do...)

Start: 6e Dec 2023
MFL
"""

from tkinter import *
from GraphFrame import GraphFrame
from TelemetryControls import ReadOut
from MapFrame import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import messagebox
from Styles import Colors
from time import monotonic
from TelemetryDecoder import DecoderState
from TelemetryReader import SDCardFileReader, RadioTelemetryReader, BinaryFileReader
from TelemetrySender import TelemetryTestSender
from enum import Enum
from matplotlib import style
import queue
style.use('dark_background')

FAST_UPDATE_INTERVAL = 10
GRAPH_UPDATE_INTERVAL = 100 # time between updating graphs
RECENT_PACKET_TIMEOUT = 1000 # ms after receiving last message that we show red marker to user
TIME_SINCE_FORMAT = "{:.2f}"

NUM_COLS = 6
NUM_ROWS = 3
PADX = 4
PADY = 4

SASH_WIDTH = 10
CELL_WIDTH = 220

"""
Work list:
1.  CSV format like ground station CSV format
2.  Faster graph rendering
3.  Add log window
4.  Add min to readout
5.  Click on GPS lat/lon to make map move there
6.  Event colors: 18 to 21,26,28 red color. Range 8-5 green.
7.  Add online/offline toggle to map itself
8.  Add download current area to map itself
"""

class AppState(Enum):
    IDLE = 0
    READING_FILE = 1
    READING_SERIAL = 2
    RECORDING_SERIAL = 3

class TelemetryApp(Tk):
    def __init__(self,
                 screenName: str | None = None,
                 baseName: str | None = None,
                 className: str = "Tk",
                 useTk: bool = True,
                 sync: bool = False,
                 use: str | None = None) -> None:

        super().__init__(screenName, baseName, className, useTk, sync, use)

        self.state = AppState.IDLE

        self.message_queue = queue.Queue() # incoming telemetry from file or serial port

        self.telemetry_vars = ["name",
                               "time", "accelX", "accelY", "accelZ", "gyroZ" "highGx", "highGy", "highGz",
                               "smoothHighGz", "offVert", "intVel", "intAlt", "fusionVel", "fusionAlt",
                               "fltEvents", "radioCode", "baroAlt", "altMoveAvg", "gnssLat", "gnssLon",
                               "landing_latitude", "landing_longitude", "landing_time",
                               "launch_latitude", "launch_longitude", "launch_time", "gnssFix",
                               "gnssSpeed", "gnssAlt", "gnssAngle", "gnssSatellites", "radioPacketNum"]

        """
        priority variables are always updated when a new message comes in
        (vars not in this list overwrite the last known value and only update at
        the selected frame rate)
        """
        self.priority_vars = ["time", "name", "accelZ", "fusionAlt", "fusionVel"]

        for var in self.telemetry_vars:
            self.setvar(var)

        self.serial_reader = RadioTelemetryReader(self.message_queue)
        self.serial_reader.name = "serial_reader"
        self.csv_file_reader = SDCardFileReader(self.message_queue)
        self.csv_file_reader.name = "csv_file_reader"
        self.tlm_file_reader = BinaryFileReader(self.message_queue)
        self.tlm_file_reader.name = "tlm_file_reader"

        self.fast_update_timer = None # used to store tk.after ID for text updating
        self.slow_update_timer = None # used to store tk after ID for graph updating
        self.currently_receiving_timer = None # used for storing tk.after ID for

        self.last_packet_local_timestamp = 0.0

        self.offline_maps_only = BooleanVar(self, True, "offline_maps_only")
        self.telemetry_state = DecoderState.OFFLINE
        self.telemetry_state_name = StringVar(self, str(self.telemetry_state), "telemetryStateName")
        self.currently_receiving = BooleanVar(self, False, "currently_receiving")
        self.time_since_last_packet = StringVar(self, "0.0", "time_since_last_packet") # must be string for formating
        self.total_bytes_read = StringVar(self, "0B", "total_bytes_read")
        self.total_messages_decoded = IntVar(self, 0, "total_messages_decoded")

        self.test_serial_sender = TelemetryTestSender() # for test data only


        """
        Window properties
        -----------------
        """
        self.title("HPR Telemetry Viewer")
        self.config(background=Colors.BG_COLOR)

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (w, h))


        """
        Menu Bar
        --------
        """
        self.menubar = Menu(self)
        self.config(menu=self.menubar)

        self.file_menu = Menu(self.menubar)
        self.file_menu.add_command(label="Open", command=self.open_telemetry_file)
        self.file_menu.add_command(label="Reset", command=self.reset)
        self.file_menu.add_command(label='Exit', command=self.destroy)

        self.map_menu = Menu(self.menubar)
        self.map_menu.add_command(label="Download current map", command=self.download_current_map)
        self.map_menu.add_command(label="Set offline map path", command=self.set_offline_path)
        self.map_menu.add_command(label="Delete map", command=self.delete_map)

        self.map_menu.add_checkbutton(label="Only use offline maps",
                                      variable=self.offline_maps_only)

        self.serial_menu = Menu(self.menubar)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.menubar.add_cascade(label="Serial", menu=self.serial_menu)
        self.menubar.add_cascade(label="Map", menu=self.map_menu)

        self.update_serial_menu()


        """
        Window panes
        ------------
        """
        self.window = PanedWindow(orient="horizontal", background="#aaaaaa")
        self.window.configure(sashwidth=SASH_WIDTH)
        self.readouts = Frame(self.window, width=CELL_WIDTH*2, background=Colors.BG_COLOR)
        self.graphs = Frame(self.window, width=400, background="black")
        self.map_column = MapColumn(self.window)

        self.window.add(self.readouts)
        self.window.add(self.graphs, stretch="always")
        self.window.add(self.map_column)

        self.window.pack(fill="both", expand=True)

        self.window.sash_place(0, CELL_WIDTH, 0)
        self.window.sash_place(1, CELL_WIDTH, 0)

        self.download_overlay = None # Used to blank the UI when map download is happen


        """
        Readouts Column
        ---------------
        Left side
        """
        self.altitude = ReadOut(self.readouts, "Altitude", "fusionAlt", "m", "ft", ReadOut.metresToFeet, color=Colors.ALTITUDE_COLOR)
        self.altitude.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=(N,E,W,S))
        self.altitude.config(width = CELL_WIDTH)

        self.velocity = ReadOut(self.readouts, "Velocity", "fusionVel", "m/s", "mi/h", ReadOut.msToMph, color=Colors.VELOCITY_COLOR)
        self.velocity.grid(row=1, column=0, padx=PADX, pady=PADY, sticky=(N,S))
        self.velocity.config(width = CELL_WIDTH)

        self.acceleration = ReadOut(self.readouts, "Accel", "accelZ", "m/s/s", "G", ReadOut.mssToG, color=Colors.ACCELERATION_COLOR)
        self.acceleration.grid(row=2, column=0, padx=PADX, pady=PADY, sticky=(N,S))
        self.acceleration.config(width = CELL_WIDTH)

        self.readouts.columnconfigure(0, weight=1)
        for i in range (NUM_ROWS):
            self.readouts.rowconfigure(i, weight=1)


        """
        Graphs Column
        -------------
        Centre
        """
        self.altitude_graph = GraphFrame(self.graphs,
                                         "m",
                                         DoubleVar(self, 0.0, "time"),
                                         DoubleVar(self, 0.0, "fusionAlt"),
                                         None,
                                         Colors.ALTITUDE_COLOR)
        self.altitude_graph.grid(row=0, column=0, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))

        self.velocity_graph = GraphFrame(self.graphs,
                                         "m/s",
                                         DoubleVar(self, 0.0, "time"),
                                         DoubleVar(self, 0.0, "fusionVel"),
                                         None,
                                         Colors.VELOCITY_COLOR)
        self.velocity_graph.grid(row=1, column=0, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))

        self.acceleration_graph = GraphFrame(self.graphs,
                                             "m/s/s",
                                             DoubleVar(self, 0.0, "time"),
                                             DoubleVar(self, 0.0, "accelZ"),
                                             (-20.0, 80.0),
                                             Colors.ACCELERATION_COLOR)
        self.acceleration_graph.grid(row=2, column=0, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.graphs.columnconfigure(0, weight=1)

        for i in range (NUM_ROWS):
            self.graphs.rowconfigure(i, weight=1)

        # Must be after setup because it affects the grid
        self.set_telemetry_state(DecoderState.OFFLINE)


        """
        Keyboard shortcuts
        ------------------
        """
        self.bind('1', lambda _: self.test_serial_sender.send_single_packet(TelemetryTestSender.PRE_FLIGHT_TEST))
        self.bind('2', lambda _: self.test_serial_sender.send_single_packet(TelemetryTestSender.PRE_FLIGHT_TEST_2))
        self.bind('3', lambda _: self.test_serial_sender.send_single_packet(TelemetryTestSender.IN_FLIGHT_TEST))
        self.bind('4', lambda _: self.test_serial_sender.send_single_packet(TelemetryTestSender.POST_FLIGHT_TEST))

        self.bind('q', lambda _: self.quit())
        self.bind('s', lambda _: print(self.serial_reader.available_ports()))
        self.bind('r', lambda _: self.reset())
        self.bind('t', lambda _: self.open_telemetry_test_file())
        self.focus()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.reset()

    def set_telemetry_state(self, state: DecoderState) -> None:
        if state != self.telemetry_state:
            print(f"Changing state to {str(state)}")
            self.telemetry_state = state
            self.telemetry_state_name.set(f"{str(state).upper()}")
            self.map_column.set_state(state)


    def on_closing(self):
        if self.confirm_stop():
            self.destroy()
            self.quit()

    def update(self):
        self.time_since_last_packet.set(TIME_SINCE_FORMAT.format((monotonic() - self.last_packet_local_timestamp)))

        try:
            while True:
                message = self.message_queue.get(block=False)
                self.reset_packet_timer()
                self.message_callback(message)
                self.map_column.update()
                self.altitude_graph.update()
                self.acceleration_graph.update()
                self.velocity_graph.update()

        except queue.Empty:
            pass
        finally:
            if self.csv_file_reader.running.is_set() or self.serial_reader.running.is_set() or self.tlm_file_reader.running.is_set():
                self.fast_update_timer = self.after(FAST_UPDATE_INTERVAL, self.update)
            else:
                self.stop()


    def update_graph(self):
        self.altitude_graph.render()
        self.acceleration_graph.render()
        self.velocity_graph.render()

        self.slow_update_timer = self.after(GRAPH_UPDATE_INTERVAL, self.update_graph)


    def message_callback(self, message):
        """
        decodes FC-style message into app variables and triggers graphs + map to update
        """
        self.set_telemetry_state(message.decoder_state)
        self.total_bytes_read.set(self.format_bytes(message.total_bytes))
        self.total_messages_decoded.set(message.total_messages)
        self.last_packet_local_timestamp = message.local_time

        for (key, value) in message.telemetry.items():
            self.setvar(key, value)


    def reset_packet_timer(self):
        self.currently_receiving.set(True)

        if self.currently_receiving_timer is not None:
            self.after_cancel(self.currently_receiving_timer)

        self.currently_receiving_timer = self.after(RECENT_PACKET_TIMEOUT, lambda: self.currently_receiving.set(False))


    def confirm_stop(self) -> bool:
        """
        stops recording and/or playing back serial or file
        but does not reset the graphs and map e.t.c.

        return true if user decided to stop, false if they canceled
        """
        okcancel = True

        match self.state:
            case AppState.IDLE:
                pass

            case AppState.READING_FILE:
                okcancel = messagebox.askokcancel("Stop Reading",
                                                  "This will stop the playback of this file, are you sure?")

            case AppState.READING_SERIAL:
                okcancel = messagebox.askokcancel("Stop Listening",
                                                  "This will disconnect from current serial port, are you sure?")

            case AppState.RECORDING_SERIAL:
                okcancel = messagebox.askokcancel("Stop Recording",
                                                  "This will disconnect and stop recording current serial port, are you sure?")

        if okcancel:
            self.stop()

        return okcancel

    def start(self):
        self.last_packet_local_timestamp = monotonic()
        self.update()
        self.update_graph()

    def stop(self):
        if self.fast_update_timer is not None:
            self.after_cancel(self.fast_update_timer)
            self.fast_update_timer = None

        if self.slow_update_timer is not None:
            self.after_cancel(self.slow_update_timer)
            self.slow_update_timer = None

        # stop file decoder if it's running
        self.csv_file_reader.stop()
        # stop serial decoder if it's running
        self.serial_reader.stop()
        # update status display to show we are now disconnected
        self.map_column.set_status_text("Disconnected", Colors.LIGHT_GRAY)

        self.state = AppState.IDLE

    def reset(self) -> None:
        """
        resets the app back to zero and stops recording or playback
        for when loading new file or connecting to new serial port
        """
        if self.confirm_stop():
            self.stop()

        # clear all telemetry variables:
        for var in self.telemetry_vars:
            self.setvar(var, "0")

        self.set_telemetry_state(DecoderState.OFFLINE)
        self.time_since_last_packet.set(TIME_SINCE_FORMAT.format(float(0)))

        # clear app variables and graphs:
        self.setvar("name", "")
        self.map_column.reset()
        self.altitude_graph.reset()
        self.velocity_graph.reset()
        self.acceleration_graph.reset()

    def update_serial_menu(self) -> None:
        """
        scans for serial ports and updates menu to show detected ports
        """
        self.serial_menu.delete(0, END)

        self.serial_menu.add_command(label="Disconnect", command=self.confirm_stop)

        ports = self.serial_reader.available_ports()

        if len(ports) == 0:
            self.serial_menu.add_command(label="No serial ports", state=DISABLED)
        else:
            for port_name in ports:
                self.serial_menu.add_command(label=port_name, command=lambda name=port_name: self.listen_to_port(name))

        self.serial_menu.add_separator()
        self.serial_menu.add_command(label="Re-scan", command=self.update_serial_menu)

    def listen_to_port(self, port):
        if self.confirm_stop():
            self.reset() # if user has decided to cancel current operation then we should also reset

        if port in self.serial_reader.available_ports():
            yesnocancel = messagebox.askyesnocancel(f"Listen on serial port {port}",
                                                    "Do you want to save a backup of this telemetry to disk?")

            if yesnocancel is None:
                return

            self.reset()

            if yesnocancel:
                filename = asksaveasfilename(title="Choose backup file name", defaultextension=".tlm", filetypes =[('Binary Telemetry Data', '*.tlm')])
                if filename != "":
                    self.serial_reader.filename = filename
                    self.state = AppState.RECORDING_SERIAL
                    self.map_column.set_status_text(f"Recording serial port {port}", Colors.WHITE, Colors.DARK_RED)
                else:
                    return
            else:
                print(f"Not saving telemetry from serial port {port} to file")
                self.state = AppState.READING_SERIAL
                self.map_column.set_status_text(f"Listening to {port} (Not Recording)", Colors.WHITE, "dark blue")

            self.serial_reader.serial_port = port
            self.serial_reader.start()
            self.start()

    def open_telemetry_file(self):
        if self.confirm_stop():
            self.reset() # if user has decided to cancel current operation then we should also reset

        filename = askopenfilename(filetypes =[('Telemetry Binary Files', '*.tlm'),
                                               ('Telemetry Text Files', '*.csv')])

        if filename.endswith(".tlm"):
            self.reset()
            self.tlm_file_reader.filename = filename
            self.state = AppState.READING_FILE
            self.map_column.set_status_text(f"Playing: {filename.split('/')[-1]}", Colors.WHITE, Colors.DARK_GREEN)
            self.tlm_file_reader.start()
            self.start()

        if filename.endswith(".csv"):
            self.reset()
            self.csv_file_reader.filename = filename
            self.state = AppState.READING_FILE
            self.map_column.set_status_text(f"Playing: {filename.split('/')[-1]}", Colors.WHITE, Colors.DARK_GREEN)
            self.csv_file_reader.start()
            self.start()

    def open_telemetry_test_file(self):
        filename = askopenfilename(filetypes =[('Telemetry Text Files', '*.csv'), ('Other Telemetry Files', '*.*')])
        if filename != "":
            self.test_serial_sender.stop()
            self.test_serial_sender.serial_port = "COM3"
            self.test_serial_sender.filename = filename
            self.test_serial_sender.start()

    def download_current_map(self):
        if not self.confirm_stop():
            return

        try:
            self.download_overlay = Frame(self.window, background="#0f0f0f")
            self.download_overlay.place(relwidth=1, relheight=1)

            ok = messagebox.askokcancel("Download current map",
                                        "This will currently displayed location at all zoom levels. Depending on internet connection this require take several minutes.\n\nDuring download the app will be unresponsive.\n\nAre you sure you wish to continue?")

            if not ok:
                return

            self.map_column.download_current_map()

        except Exception as e:
            messagebox.showerror("Downloading Error",
                                 f"Unable to download map, check internet connection\n\n({e})")
            return

        else:
            messagebox.showinfo("Downloading Successful",
                                f"Saved current location to database: {self.map_column.database_path}")

        finally:
            self.download_overlay.destroy()
            self.download_overlay = None


    def set_offline_path(self):
        if not self.confirm_stop():
            return

        filename = askopenfilename(filetypes =[('Map Database', '*.db'), ('Other Files', '*.*')])
        if filename is not None and filename != "":
            print(f"Attempting to load map file: {filename}")
            self.map_column.load_offline_database(filename)

    def delete_map(self):
        self.map_column.delete_map()

    @staticmethod
    def format_bytes(size):
        power = 10**3

        if size < power:
            return f"{size}B"

        n = 0
        power_labels = {0 : '', 1: 'k', 2: 'M', 3: 'G', 4: 'T'}

        while size > power:
            size /= power
            n += 1

        return "{:.3f}".format(size)[:5] + power_labels[n] + "B"


if __name__ == "__main__":
    telemetry = TelemetryApp()
    telemetry.mainloop()
    telemetry.quit()

