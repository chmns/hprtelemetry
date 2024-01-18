"""
Telemetry viewer for HPR flight computer by SparkyVT

This will accept radio packet data and display on a laptop or PC
either from COM port (RFD900 with FDTI) ou Teensy USB output (to do...)

Start: 6e Dec 2023
MFL

Todo:
Preflight  }
Inflight   } GPS lat lon alt
Postflight }
Number of SATs

max alt
max vel
max G
max GPS alt
"""

from tkinter import *
import tkintermapview
from GraphFrame import GraphFrame
from TelemetryControls import *
import TelemetryDecoder
from matplotlib import style
style.use('dark_background')

window = Tk()
window.title("Telemetry Viewer")
window.config(background="#222222")
w, h = window.winfo_screenwidth(), window.winfo_screenheight()
window.geometry("%dx%d+0+0" % (w, h))

test_runner = TelemetryDecoder.TestTelemetry()

NUM_COLS = 7
NUM_ROWS = 3
PADX = 4
PADY = 4

ALTITUDE_COLOR = "#8BD3E6"
VELOCITY_COLOR = "#FF6D6A"
ACCELERATION_COLOR = "#EFBE7D"

COORDS_FONT = "Courier 24 bold"
DEFAULT_COORD = "0.0000000"
PREFLIGHT_COORDS_PREFIX = "Pre: "
CURRENT_COORDS_PREFIX = "Curr:"
POSTFLIGHT_COORDS_PREFIX = "Post:"
#orange: #EFBE7D

for col in range (NUM_COLS):
    # test = Frame(window)
    # test.grid(row=col%NUM_ROWS, column=col, padx=PADX, pady=PADY, sticky=(N,E,S,W))    
    window.columnconfigure(col, weight=0)

window.columnconfigure(1, weight=1)

for row in range(NUM_ROWS):
    window.rowconfigure(row, weight=1)

# for col in range(3):
    # test = ReadOut(window, " ", " ", " ")
    # test.grid(row=2, column=col+4, padx=PADX, pady=PADY, sticky=(N,E,S,W))    

CELL_WIDTH = 280

altitude = ReadOut(window, "Altitude", "m", "ft", ReadOut.metresToFeet, ALTITUDE_COLOR)
altitude.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=(N,S))
altitude.config(width = CELL_WIDTH)
altitude.grid_propagate(False)

velocity = ReadOut(window, "Velocity", "m/s", "mi/h", ReadOut.msToMph, VELOCITY_COLOR)
velocity.grid(row=1, column=0, padx=PADX, pady=PADY, sticky=(N,S))
velocity.config(width = CELL_WIDTH)
velocity.grid_propagate(False)

acceleration = ReadOut(window, "Acceleration", "m/s/s", "G", ReadOut.mssToG, ACCELERATION_COLOR)
acceleration.grid(row=2, column=0, padx=PADX, pady=PADY, sticky=(N,S))
acceleration.config(width = CELL_WIDTH)
acceleration.grid_propagate(False)

altitude_graph = GraphFrame(window, "m", ALTITUDE_COLOR)
altitude_graph.grid(row=0, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
altitude_graph.grid_propagate(True)

velocity_graph = GraphFrame(window, "m/s", VELOCITY_COLOR)
velocity_graph.grid(row=1, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
velocity_graph.grid_propagate(True)

acceleration_graph = GraphFrame(window, "m/s/s", ACCELERATION_COLOR, (-20.0, 80.0))
acceleration_graph.grid(row=2, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
acceleration_graph.grid_propagate(True)


map_frame = Frame(window, bg="blue")
map_frame.grid(row=0, column=4, rowspan=2, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))
map_frame.grid_propagate(False)
map_frame.columnconfigure(0, weight=1)
map_frame.rowconfigure(0, weight=1)
map_frame.rowconfigure(1, weight=0)

map = tkintermapview.TkinterMapView(map_frame)
map.grid(row=0, column=0, sticky=(N,E,S,W))
map.lat = 44.7916443
map.lon = -0.5995578
map.set_position(map.lat,map.lon)
map.set_zoom(14)
map.grid_propagate(True)

preflight_coords = Label(map_frame, text=f"{PREFLIGHT_COORDS_PREFIX} {DEFAULT_COORD} {DEFAULT_COORD}", bg="#0F0F0F", fg="#FFFFFF", font=COORDS_FONT)
preflight_coords.grid(row=1, column=0, sticky=(E,W))
preflight_coords.grid_propagate(False)

current_coords = Label(map_frame, text=f"{CURRENT_COORDS_PREFIX} {DEFAULT_COORD} {DEFAULT_COORD}", bg="#0F0F0F", fg="#FFFFFF", font=COORDS_FONT)
current_coords.grid(row=2, column=0, sticky=(E,W))
current_coords.grid_propagate(False)
 
postflight_coords = Label(map_frame, text=f"{POSTFLIGHT_COORDS_PREFIX} {DEFAULT_COORD} {DEFAULT_COORD}", bg="#0F0F0F", fg="#FFFFFF", font=COORDS_FONT)
postflight_coords.grid(row=3, column=0, sticky=(E,W))
postflight_coords.grid_propagate(False)


tilt_spin = TiltAndSpin(window)
tilt_spin.grid(row=2, column=4, padx=PADX, pady=PADY, sticky=(N,E,S,W))
tilt_spin.config(width = CELL_WIDTH)
tilt_spin.grid_propagate(False)

status = TelemetryStatus(window)
status.grid(row=2, column=5, padx=PADX, pady=PADY, sticky=(N,E,S,W))
status.config(width = CELL_WIDTH)
status.grid_propagate(False)

controls = TelemetryControls(window)
controls.grid(row=2, column=6, padx=PADX, pady=PADY, sticky=(N,E,S,W))
controls.config(width = CELL_WIDTH)
controls.grid_propagate(False)

def prelaunch_callback(prelaunch):
    status.set_name(prelaunch["RocketName"])
    preflight_coords.config(text=f"{PREFLIGHT_COORDS_PREFIX} {map.lat} {map.lon}")
    map.set_marker(prelaunch["gpsLat"], prelaunch["gpsLon"], f"Pre")

def postflight_callback(postflight):
    pass

def message_callback(message):
    event_type = int(message["event"])
    controls.update_value(event_type)

    acceleration_value = message["acceleration"]
    acceleration.update_value(acceleration_value, event_type < 4)
    acceleration_graph.append(acceleration_value)

    velocity_value = message["velocity"]
    velocity.update_value(velocity_value)
    velocity_graph.append(velocity_value)

    altitude_value = message["altitude"]
    altitude.update_value(altitude_value)
    altitude_graph.append(altitude_value)

    tilt_spin.update_value(message["tilt"], message["spin"])

    status.update_value(message["packetNum"],
                        message["time"],
                        message["signalStrength"])

    new_lat = message["gpsLat"]
    new_lon = message["gpsLon"]
    if new_lat != map.lat or new_lon != map.lon:
        map.lat = new_lat
        map.lon = new_lon
        map.set_position(map.lat, map.lon, marker=True)
        current_coords.config(text=f"{CURRENT_COORDS_PREFIX} {map.lat} {map.lon}")

test_runner.prelaunch_callback = prelaunch_callback
test_runner.message_callback = message_callback

window.bind('t', lambda e: test_runner.start())
window.bind('q', lambda e: window.quit())
window.focus()

def on_closing():
    window.destroy()
    window.quit()

window.protocol("WM_DELETE_WINDOW", on_closing)

window.mainloop()
window.quit()
