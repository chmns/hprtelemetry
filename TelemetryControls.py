from tkinter import *
from PIL import ImageTk, Image

def metresToFeet(metres):
    return metres / 3.281

def mssToG(mss):
    return mss/9.81

def kphToMph(kph):
    return (kph/8) * 5

def default(arg):
    return arg

BG_COLOR = "#0f0f0f"
FG_COLOR = "#eeeeee"

class ReadOut(Frame):
    def __init__(self,
                 master,
                 name: str,
                 units1: str,
                 units2: str,
                 conversion: callable = default,
                 color: str = FG_COLOR):
        
        Frame.__init__(self, master, bg=BG_COLOR)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.name = name
        self.value = 0
        self.max = 0
        self.units1 = units1
        self.units2 = units2
        self.conversion = conversion
        self.color = color

        self.main = Label(self, text=f'{self.value} {self.units1}', fg=FG_COLOR, bg=BG_COLOR, font=("Arial", 48))
        self.main.grid(column = 0, row = 1, sticky = (N,E,S,W))
        
        self.name = Label(self, text=self.name, fg=self.color, bg=BG_COLOR, font="Arial 18 bold")
        self.name.grid(column = 0, row = 2, sticky=(N,E,S,W))
        
        self.max = Label(self, text=f'Max: {self.max}{units1}', fg=FG_COLOR, bg=BG_COLOR, font=("Arial", 14))
        self.max.grid(column = 0, row = 4, sticky=(N,E,S,W))


class TiltAndSpin(Frame):
    SPACING = 30

    def __init__(self, master):
        Frame.__init__(self, master, background=BG_COLOR)

        self.grid_rowconfigure(0, weight=1)
        # self.grid_rowconfigure(1, weight=2)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.tilt = Label(self, text="0 °", fg=FG_COLOR, bg=BG_COLOR, font="Arial 24 bold")
        self.tilt.grid(column = 0, row = 1, sticky = (N,E,S,W))
        
        self.tilt_label = Label(self, text="Tilt", fg=FG_COLOR, bg=BG_COLOR, font="Arial 18 bold")
        self.tilt_label.grid(column = 0, row = 2, sticky = (N,E,S,W))
        
        self.spin = Label(self, text="0 °/sec", fg=FG_COLOR, bg=BG_COLOR, font="Arial 24 bold")
        self.spin.grid(column = 0, row = 3, sticky=(N,E,S,W), pady = (TiltAndSpin.SPACING, 0))
        
        self.spin_label = Label(self, text="Spin", fg=FG_COLOR, bg=BG_COLOR, font="Arial 18 bold")
        self.spin_label.grid(column = 0, row = 4, sticky=(N,E,S,W))



class TelemetryStatus(Frame):
    SPACING = 30

    def __init__(self, master):
        Frame.__init__(self, master, background=BG_COLOR)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.packets_received = Label(self, text="234", fg=FG_COLOR, bg=BG_COLOR, font="Arial 18")
        self.packets_received.grid(column = 0, row = 1, sticky = (N,E,S,W), pady=(TelemetryStatus.SPACING,0))
        
        self.packets_received_label = Label(self, text="Packets Received", fg=FG_COLOR, bg=BG_COLOR, font="Arial 14 bold")
        self.packets_received_label.grid(column = 0, row = 2, sticky = (N,E,S,W))

        self.last_timestamp = Label(self, text="12:34:56::78", fg=FG_COLOR, bg=BG_COLOR, font="Arial 18")
        self.last_timestamp.grid(column = 0, row = 3, sticky = (N,E,S,W), pady=(TelemetryStatus.SPACING,0))

        self.last_timestamp_label = Label(self, text="Last Timestamp", fg=FG_COLOR, bg=BG_COLOR, font="Arial 14 bold")
        self.last_timestamp_label.grid(column = 0, row = 4, sticky = (N,E,S,W))
        
        self.rssi = Label(self, text="-90dB", fg=FG_COLOR, bg=BG_COLOR, font="Arial 18")
        self.rssi.grid(column = 0, row = 5, sticky=(N,E,S,W), pady=(TelemetryStatus.SPACING,0))
        
        self.rssi_label = Label(self, text="RSSI", fg=FG_COLOR, bg=BG_COLOR, font="Arial 14 bold")
        self.rssi_label.grid(column = 0, row = 6, sticky=(N,E,S,W))

class TelemetryControls(Frame):
    SPACING = 30

    def __init__(self, master):
        Frame.__init__(self, master, background=BG_COLOR)
