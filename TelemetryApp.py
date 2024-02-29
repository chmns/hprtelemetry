"""
Telemetry viewer for HPR flight computer by SparkyVT

This will accept radio packet data and display on a laptop or PC
either from COM port (RFD900 with FDTI) ou Teensy USB output (to do...)

Start: 6e Dec 2023
MFL
"""

import sys
import glob
import serial
from tkinter import *
import tkintermapview
from GraphFrame import GraphFrame
from TelemetryControls import *
from tkinter.filedialog import askopenfile
from TelemetryDecoder import TelemetryTester
from matplotlib import style
style.use('dark_background')

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

class TelemetryApp(Tk):
    def __init__(self,
                 screenName: str | None = None,
                 baseName: str | None = None,
                 className: str = "Tk",
                 useTk: bool = True,
                 sync: bool = False,
                 use: str | None = None) -> None:
    
        super().__init__(screenName, baseName, className, useTk, sync, use)

        self.test_runner = TelemetryTester("test_data\\FLIGHT10-short.csv")
        self.test_runner.decoder.message_callback = print #self.message_callback

        self.title("HPR Telemetry Viewer")
        self.config(background="#222222")
        
        w, h = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry("%dx%d+0+0" % (w, h))

        # create a menubar
        self.menubar = Menu(self)
        self.config(menu=self.menubar)

        file_menu = Menu(self.menubar)
        file_menu.add_command(label="Open", command=self.open_telemetry_file)
        file_menu.add_command(label='Exit', command=self.destroy)

        self.serial_menu = Menu(self.menubar)
        self.menubar.add_cascade(label="File", menu=file_menu)

        current_serial = StringVar(self, name="current_serial", value=None)

        # fixed column widths
        for col in range (NUM_COLS):
            self.columnconfigure(col, weight=0)

        # single column expands with width:
        self.columnconfigure(1, weight=1)

        # fixed row heights
        for row in range(NUM_ROWS):
            self.rowconfigure(row, weight=1)
        

        self.altitude = ReadOut(self, "Altitude", "m", "ft", ReadOut.metresToFeet, ALTITUDE_COLOR)
        self.altitude.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=(N,S))
        self.altitude.config(width = CELL_WIDTH)
        self.altitude.grid_propagate(False)

        self.velocity = ReadOut(self, "Velocity", "m/s", "mi/h", ReadOut.msToMph, VELOCITY_COLOR)
        self.velocity.grid(row=1, column=0, padx=PADX, pady=PADY, sticky=(N,S))
        self.velocity.config(width = CELL_WIDTH)
        self.velocity.grid_propagate(False)

        self.acceleration = ReadOut(self, "Acceleration", "m/s/s", "G", ReadOut.mssToG, ACCELERATION_COLOR)
        self.acceleration.grid(row=2, column=0, padx=PADX, pady=PADY, sticky=(N,S))
        self.acceleration.config(width = CELL_WIDTH)
        self.acceleration.grid_propagate(False)

        self.altitude_graph = GraphFrame(self, "m", ALTITUDE_COLOR)
        self.altitude_graph.grid(row=0, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.altitude_graph.grid_propagate(True)

        self.velocity_graph = GraphFrame(self, "m/s", VELOCITY_COLOR)
        self.velocity_graph.grid(row=1, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.velocity_graph.grid_propagate(True)

        self.acceleration_graph = GraphFrame(self, "m/s/s", ACCELERATION_COLOR, (-20.0, 80.0))
        self.acceleration_graph.grid(row=2, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.acceleration_graph.grid_propagate(True)


        self.map_frame = Frame(self, bg="blue")
        self.map_frame.grid(row=0, column=4, rowspan=2, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.map_frame.grid_propagate(False)
        self.map_frame.columnconfigure(0, weight=1)
        self.map_frame.rowconfigure(0, weight=1)
        self.map_frame.rowconfigure(1, weight=0)

        self.map = tkintermapview.TkinterMapView(self.map_frame)
        # map = Frame(map_frame)
        self.map.grid(row=0, column=0, sticky=(N,E,S,W))
        self.map.lat = 44.7916443
        self.map.lon = -0.5995578
        self.map.set_position(self.map.lat,self.map.lon)
        self.map.set_zoom(14) 
        self.map.grid_propagate(True)

        # location_grid = Label(map_frame)
        # self.location_grid.config(text="HASHASHAS")
        self.location_grid = LocationGrid(self.map_frame)
        self.location_grid.grid(row=1, column=0, sticky=(N,E,S,W))
        self.location_grid.grid_propagate(False)
        # self.location_grid.config(width=400)

        self.tilt_spin = TiltAndSpin(self)
        self.tilt_spin.grid(row=2, column=4, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.tilt_spin.config(width = CELL_WIDTH)
        self.tilt_spin.grid_propagate(False)

        self.status = TelemetryStatus(self)
        self.status.grid(row=2, column=5, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.status.config(width = CELL_WIDTH)
        self.status.grid_propagate(False)
        
        self.test_runner.decoder.name_callback = self.status.set_name

        self.controls = TelemetryControls(self)
        self.controls.grid(row=2, column=6, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        self.controls.config(width = CELL_WIDTH)
        self.controls.grid_propagate(False)

        self.bind('t', lambda _: self.test_runner.start())
        self.bind('q', lambda _: self.quit())
        self.bind('s', lambda _: print(self.serial_ports()))
        self.focus()

        def on_closing():
            self.destroy()
            self.quit()

        self.protocol("WM_DELETE_WINDOW", on_closing)       

    def message_callback(self, message):
        """
        list of desired keys

        keys = ["fusionVel", "fusionAlt", "numSats"]

        variables = {key: StringVar("-") for key in keys}

        on_message_received(dict):
            variables[""]

        """
        pass
            
    def update_serial_menu(self):
        self.serial_menu.delete(0, END)

        ports = self.serial_ports()

        if len(ports) == 0:
            self.serial_menu.add_command("No serial ports", state=DISABLED)
        else:
            for port in ports:
                self.serial_menu.add_command(label=port, command=print)
        
        self.serial_menu.add_separator()
        self.serial_menu.add_command(label="Re-scan", command=self.update_serial_menu)

        self.menubar.add_cascade(label="Serial Port", menu=self.serial_menu)
    

    def serial_ports(self):
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
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
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result

    def open_telemetry_file(self):
        file = askopenfile(mode ='r', filetypes =[('Telemetry Text Files', '*.txt'), ('Other Telemetry Files', '*.*')])
        if file is not None:
            self.test_runner.file = file
            self.test_runner.start()





if __name__ == "__main__":
    telemetry = TelemetryApp()
    telemetry.mainloop()
    telemetry.quit()

