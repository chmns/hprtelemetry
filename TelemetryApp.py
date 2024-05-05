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
STATS_INTERVAL = 500 # ms between calculating the bytes/second value
TIME_SINCE_FORMAT = "{:.2f}"

RECENT_PACKET_TIMEOUT = 1 # seconds after receiving last message that we show red marker to user

PROFILING = False # set to True and press 's' key during app running to see memory use

NUM_COLS = 6
NUM_ROWS = 3
PADX = 4
PADY = 4

SASH_WIDTH = 10
CELL_WIDTH = 220

"""
Work list
---------
1. Show baro alt in UI
2. Add minimim to accel / alt / velocity indicator
3. Event colors: 18 to 21,26,28 red color. Range 8-5 green.
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

        for var in self.telemetry_vars:
            self.setvar(var)

        self.serial_reader = RadioTelemetryReader(self.message_queue)
        self.serial_reader.name = "serial_reader"
        self.csv_file_reader = SDCardFileReader(self.message_queue)
        self.csv_file_reader.name = "csv_file_reader"
        self.tlm_file_reader = BinaryFileReader(self.message_queue)
        self.tlm_file_reader.name = "tlm_file_reader"

        self.current_reader = None

        self.fast_update_timer = None # used to store tk.after ID for text updating
        self.slow_update_timer = None # used to store tk after ID for graph updating
        self.currently_receiving_timer = None # used for storing tk.after ID for
        self.stats_timer = None

        self.last_packet_local_timestamp = 0.0

        self.enable_graph = BooleanVar(self, True, name="enable_graph")
        self.offline_maps_only = BooleanVar(self, True, "offline_maps_only")
        self.telemetry_state = DecoderState.OFFLINE
        self.telemetry_state_name = StringVar(self, str(self.telemetry_state), "telemetryStateName")
        self.currently_receiving = BooleanVar(self, False, "currently_receiving")
        self.time_since_last_packet = StringVar(self, "0.0", "time_since_last_packet") # must be string for formating
        self.total_bytes_read = StringVar(self, "0B", "total_bytes_read")
        self.total_bad_bytes_read = StringVar(self, "0B", "total_bad_bytes_read")
        self.total_messages_decoded = IntVar(self, 0, "total_messages_decoded")
        self.total_bad_messages = IntVar(self, 0, "total_bad_messages")
        self.bytes_per_sec = StringVar(self, "0B", "bytes_per_sec")
        self.messages_per_sec = StringVar(self, "0P", "messages_per_sec")

        self.bytes_counter = 0
        self.messages_counter = 0

        # Testing and debug
        # -----------------
        self.print_to_console = BooleanVar(self, False, "print_to_console")
        self.print_to_console.trace_add("write", self.update_print_to_console)
        self.test_serial_sender = TelemetryTestSender() # for test data only


        # Window properties
        # -----------------
        self.title("HPR Telemetry Viewer")
        self.config(background=Colors.BG_COLOR)

        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (w, h))


        # Menu Bar
        # --------
        self.menubar = Menu(self)
        self.config(menu=self.menubar)

        self.file_menu = Menu(self.menubar)
        self.file_menu.add_command(label="Open", command=self.open_telemetry_file)
        self.file_menu.add_command(label="Reset", command=self.reset)
        self.file_menu.add_command(label='Exit', command=self.destroy)

        self.map_menu = Menu(self.menubar)
        self.map_menu.add_command(label="Download current map", command=self.download_current_map)
        self.map_menu.add_command(label="Set offline map path", command=self.set_offline_path)

        self.map_menu.add_checkbutton(label="Only use offline maps",
                                      variable=self.offline_maps_only)

        self.serial_menu = Menu(self.menubar)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.menubar.add_cascade(label="Serial", menu=self.serial_menu)
        self.menubar.add_cascade(label="Map", menu=self.map_menu)

        self.update_serial_menu()


        # Window panes
        # ------------
        self.window = PanedWindow(orient="horizontal", background="#aaaaaa")
        self.window.configure(sashwidth=SASH_WIDTH)
        self.readouts = Frame(self.window, width=CELL_WIDTH*2, background=Colors.BG_COLOR)
        self.graphs = GraphFrame(self.window, width=400, background="black")
        self.map_column = MapColumn(self.window)

        self.window.add(self.readouts)
        self.window.add(self.graphs, stretch="always")
        self.window.add(self.map_column)

        self.window.pack(fill="both", expand=True)

        self.window.sash_place(0, CELL_WIDTH, 0)
        self.window.sash_place(1, CELL_WIDTH, 0)


        # Readouts Column
        # ---------------
        # Left side
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


        # Graphs Column
        # -------------
        # Centre

        # [Graph frame is created under 'Window Panes']
        self.enable_graph_checkbox = Checkbutton(self.graphs, variable=self.enable_graph, text="Enable Graphs", font=Fonts.MEDIUM_FONT, bg=Colors.GRAY, fg=Colors.LIGHT_GRAY, anchor=W, padx=PADX, pady=PADY)
        self.enable_graph_checkbox.place(relx=0, rely=1, x=20, y=-20, anchor=SW)


        # Final init
        # ----------
        # Must be after setup because it affects the grid
        self.set_telemetry_state(DecoderState.OFFLINE)


        # Keyboard shortcuts
        # ------------------
        # Bind keys 1-9 to test packet sending
        for i in range(9):
            self.bind(str(i+1), self.num_key_pressed)

        self.bind('q', lambda _: self.quit())
        if PROFILING:
            self.bind('s', lambda _: self.tracker.print_diff())
        self.bind('r', lambda _: self.reset())
        self.bind('t', lambda _: self.open_telemetry_test_file())
        self.focus()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.reset()


    def update_print_to_console(self, *_):
        self.serial_reader.print_received = self.print_to_console.get()


    def num_key_pressed(self, event):
        if self.serial_reader.running.is_set():
            self.test_serial_sender.send_single_packet(int(event.char)-1)


    def set_telemetry_state(self, state: DecoderState) -> None:
        if state != self.telemetry_state:
            self.telemetry_state = state
            self.telemetry_state_name.set(f"{str(state).upper()}")
            self.map_column.set_state(state)


    def on_closing(self):
        if self.confirm_stop():
            if PROFILING:
                self.tracker.print_diff()
            self.destroy()
            self.quit()

    def check_queue(self):
        """
        Check the message queue regularly to see if new messages came.
        If they came then process then.
        """
        time_since_last_packet = (monotonic() - self.last_packet_local_timestamp)

        # Set red/green indicator in status bar depending on when last packet came in:
        self.currently_receiving.set(time_since_last_packet < RECENT_PACKET_TIMEOUT)
        self.time_since_last_packet.set(TIME_SINCE_FORMAT.format(time_since_last_packet))

        try:
            while True:
                message = self.message_queue.get(block=False)
                self.process_message(message)

        except queue.Empty:
            pass

        finally:

            if self.current_reader.running.is_set():
                self.fast_update_timer = self.after(FAST_UPDATE_INTERVAL, self.check_queue)
            else:
                self.stop()


    def draw_graph(self):
        """
        Triggers matplotlib to blit received data to screen
        Data is updated even if it is not draw. So when we are not updating here we
        do not lose any graph data.
        """
        if self.enable_graph.get():
            self.graphs.draw()

        self.slow_update_timer = self.after(GRAPH_UPDATE_INTERVAL, self.draw_graph)


    def update_stats(self):
        """
        Called regularly to update data received and packets decoded statistics
        """
        interval = STATS_INTERVAL / 1000
        self.bytes_per_sec.set(f"{self.format_bytes(self.bytes_counter / interval)}")
        self.bytes_counter = 0

        self.messages_per_sec.set(round(self.messages_counter / interval))
        self.messages_counter = 0

        self.total_bad_bytes_read.set(self.format_bytes(self.current_reader.bad_bytes_received))
        self.total_bad_messages.set(self.current_reader.bad_packets_received)

        self.stats_timer = self.after(STATS_INTERVAL, self.update_stats)

    def process_message(self, message):
        """
        decodes FC-style message into app variables and triggers graphs + map to update
        """
        self.set_telemetry_state(message.decoder_state)
        self.last_packet_local_timestamp = message.local_time

        self.bytes_counter += (message.total_message_size)
        self.messages_counter += 1

        self.total_messages_decoded.set(self.current_reader.messages_decoded)
        self.total_bytes_read.set(self.format_bytes(self.current_reader.bytes_received))

        for (key, value) in message.telemetry.items():
            self.setvar(key, value)

        self.map_column.update_data()
        self.graphs.update_data()

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
        self.check_queue()
        self.draw_graph()
        self.update_stats()

    def stop(self):
        if self.fast_update_timer is not None:
            self.after_cancel(self.fast_update_timer)
            self.fast_update_timer = None

        if self.slow_update_timer is not None:
            self.after_cancel(self.slow_update_timer)
            self.slow_update_timer = None

        if self.stats_timer is not None:
            self.after_cancel(self.stats_timer)
            self.stats_timer = None

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
        self.total_bytes_read.set("0B")
        self.total_bad_bytes_read.set("0B")
        self.total_messages_decoded.set(0)
        self.total_bad_messages.set(0)
        self.bytes_per_sec.set("0B")
        self.messages_per_sec.set("0P")

        # clear app variables and graphs:
        self.setvar("name", "")
        self.map_column.reset()
        self.graphs.reset()

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
        self.serial_menu.add_checkbutton(label="Print data in console",variable=self.print_to_console)

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
                    self.map_column.set_status_text(f"Recording {port} to {os.path.basename(filename)}", Colors.WHITE, Colors.DARK_RED)
                else:
                    return
            else:
                # print(f"Not saving telemetry from serial port {port} to file")
                self.state = AppState.READING_SERIAL
                self.map_column.set_status_text(f"Listening to {port}", Colors.WHITE, Colors.DARK_BLUE)

            self.current_reader = self.serial_reader
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
            self.current_reader = self.tlm_file_reader
            self.tlm_file_reader.start()
            self.start()

        if filename.endswith(".csv"):
            self.reset()
            self.csv_file_reader.filename = filename
            self.state = AppState.READING_FILE
            self.map_column.set_status_text(f"Playing: {filename.split('/')[-1]}", Colors.WHITE, Colors.DARK_GREEN)
            self.current_reader = self.csv_file_reader
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

        download_overlay = Frame(self.window, background="#0f0f0f")
        download_overlay.place(relwidth=1, relheight=1)
        map_overlay = Frame(self.map_column, background="#0f0f0f")
        map_overlay.place(relwidth=1, relheight=1)

        ok = messagebox.askokcancel("Download current map",
                                    "This will currently displayed location at all zoom levels. Depending on internet connection this require take several minutes.\n\nDuring download the app will be unresponsive.\n\nAre you sure you wish to continue?")

        if not ok:
            download_overlay.place_forget()
            del download_overlay
            map_overlay.place_forget()
            del map_overlay
            return

        try:
            self.map_column.map_frame.download_current_map()
        except Exception as error:
            messagebox.showerror("Downloading Error",
                                f"Unable to download map: \n\n({error})")

        else:
            messagebox.showinfo("Downloading Successful",
                                f"Saved current location to database.")

        finally:
            download_overlay.place_forget()
            del download_overlay
            map_overlay.place_forget()
            del map_overlay


    def set_offline_path(self):
        if not self.confirm_stop():
            return

        filename = askopenfilename(filetypes =[('Map Database', '*.db'), ('Other Files', '*.*')])
        if filename is not None and filename != "":
            print(f"Attempting to load map file: {filename}")
            self.map_column.load_offline_database(filename)

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