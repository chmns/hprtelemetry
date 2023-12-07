"""
Telemetry viewer for HPR flight computer by SparkyVT

This will accept radio packet data and display on a laptop or PC
either from COM port (RFD900 with FDTI) ou Teensy USB output (to do...)

Start: 6e Dec 2023
MFL
"""

from tkinter import *
import tkintermapview
from GraphFrame import GraphFrame
from TelemetryControls import *
from matplotlib import style
style.use('dark_background')

window = Tk()
window.title("Telemetry Viewer")
window.config(background="#222222")
w, h = window.winfo_screenwidth(), window.winfo_screenheight()
window.geometry("%dx%d+0+0" % (w, h))

NUM_COLS = 7
NUM_ROWS = 3
PADX = 4
PADY = 4

ALTITUDE_COLOR = "#8BD3E6"
VELOCITY_COLOR = "#FF6D6A"
ACCELERATION_COLOR = "#EFBE7D"
#orange: #EFBE7D

for col in range (NUM_COLS):
    # test = Frame(window)
    # test.grid(row=col%NUM_ROWS, column=col, padx=PADX, pady=PADY, sticky=(N,E,S,W))    
    window.columnconfigure(col, weight=1)


for row in range(NUM_ROWS):
    window.rowconfigure(row, weight=1)

# for col in range(3):
    # test = ReadOut(window)
    # test.grid(row=2, column=col+4, padx=PADX, pady=PADY, sticky=(N,E,S,W))    

altitude = ReadOut(window, "Altitude", "m", "ft", metresToFeet, ALTITUDE_COLOR)
altitude.grid(row=0, column=0, padx=PADX, pady=PADY, sticky=(N,E,S,W))

velocity = ReadOut(window, "Velocity", "km/h", "mi/h", kphToMph, VELOCITY_COLOR)
velocity.grid(row=1, column=0, padx=PADX, pady=PADY, sticky=(N,E,S,W))

acceleration = ReadOut(window, "Acceleration", "m/s/s", "G", mssToG, ACCELERATION_COLOR)
acceleration.grid(row=2, column=0, padx=PADX, pady=PADY, sticky=(N,E,S,W))

altitude_graph = GraphFrame(window, "m", ALTITUDE_COLOR)
altitude_graph.grid(row=0, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))

velocity_graph = GraphFrame(window, "kph", VELOCITY_COLOR)
velocity_graph.grid(row=1, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))

acceleration_graph = GraphFrame(window, "m/s/s", ACCELERATION_COLOR)
acceleration_graph.grid(row=2, column=1, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))


map = Frame(window)
map = tkintermapview.TkinterMapView(window)
map.grid(row=0, column=4, rowspan=2, columnspan=3, padx=PADX, pady=PADY, sticky=(N,E,S,W))

tilt_spin = TiltAndSpin(window)
tilt_spin.grid(row=2, column=4, padx=PADX, pady=PADY, sticky=(N,E,S,W))

status = TelemetryStatus(window)
status.grid(row=2, column=5, padx=PADX, pady=PADY, sticky=(N,E,S,W))

controls = TelemetryControls(window)
controls.grid(row=2, column=6, padx=PADX, pady=PADY, sticky=(N,E,S,W))


def on_closing():
    window.destroy()
    window.quit()

window.protocol("WM_DELETE_WINDOW", on_closing)

window.mainloop()
