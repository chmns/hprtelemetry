from tkinter import *
from PIL import ImageTk, Image

BG_COLOR = "#0f0f0f"
FG_COLOR = "#eeeeee"

class ReadOut(Frame):
    @staticmethod
    def metresToFeet(metres):
        return metres / 3.281

    @staticmethod
    def mssToG(mss):
        return mss/9.81

    @staticmethod
    def msToMph(ms):
        return ms * 2.236936

    @staticmethod
    def msTofps(ms):
        return ms * 3.28084

    @staticmethod
    def default(arg):
        return arg

    def update_value(self, *_):
        new_value = self.variable.get() # * self.multiplier

        if new_value >= self.max_value:
            self.max_value = new_value

        # self.value = new_value
        self.main.config(text=f'{new_value:.{self.decimals}f}')
        self.max.config(text=f'Max:\n{self.max_value:.{self.decimals}f}')

    def set_final_value(self, final_value):
        self.final.config(text=f"Final:{final_value}")

    def __init__(self,
                 master,
                 name: str,
                 variable: str,
                 units1: str,
                 units2: str,
                 multiplier: int = 1,
                 conversion: callable = default,
                 color: str = FG_COLOR,
                 decimals: int = 1):

        Frame.__init__(self, master, bg=BG_COLOR)

        self.variable = DoubleVar(master, name = variable)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(6, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.name = name
        self.value = 0
        self.max_value = 0
        self.units1 = units1
        self.units2 = units2
        self.multiplier = multiplier
        self.conversion = conversion
        self.color = color
        self.decimals = decimals

        self.variable.trace_add("write", self.update_value)

        self.main = Label(self, text="0", fg=FG_COLOR, bg=BG_COLOR, font=("Arial", 48))
        # self.main = Label(self, text=f'{self.value}', fg=FG_COLOR, bg=BG_COLOR, font=("Arial", 48))
        self.main.grid(column = 0, row = 1, sticky = (N,S))

        self.name = Label(self, text=f'{self.units1} {self.name}', fg=self.color, bg=BG_COLOR, font="Arial 18 bold")
        self.name.grid(column = 0, row = 2, sticky=(N,S))

        self.max = Label(self, text=f'Max:\n{self.max_value}{units1}', fg=FG_COLOR, bg=BG_COLOR, font=("Arial", 18))
        self.max.grid(column = 0, row = 4, sticky=(N,S))

        self.final = Label(self, text="", fg=self.color, bg=BG_COLOR, font=("Arial Bold", 18))
        self.final.grid(column = 0, row = 6, sticky=(N,S))

class TiltAndSpin(Frame):
    SPACING = 30

    def update_value(self, tilt: float, spin: float) -> None:
        self.tilt.config(text=f'{tilt:.0f}°')
        self.spin.config(text=f'{spin:.0f}°/sec')

    def __init__(self, master, tilt_var: str, spin_var: str):
        Frame.__init__(self, master, background=BG_COLOR)

        self.grid_rowconfigure(0, weight=1)
        # self.grid_rowconfigure(1, weight=2)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tilt = Label(self, textvariable=DoubleVar(master, 0.0, tilt_var), fg=FG_COLOR, bg=BG_COLOR, font="Arial 32 bold")
        self.tilt.grid(column = 0, row = 1, sticky = (N,E,S,W))

        self.tilt_label = Label(self, text="Tilt", fg=FG_COLOR, bg=BG_COLOR, font="Arial 18 bold")
        self.tilt_label.grid(column = 0, row = 2, sticky = (N,E,S,W))

        self.spin = Label(self, textvariable=DoubleVar(master, 0.0, spin_var), fg=FG_COLOR, bg=BG_COLOR, font="Arial 32 bold")
        self.spin.grid(column = 0, row = 3, sticky=(N,E,S,W), pady = (TiltAndSpin.SPACING, 0))

        self.spin_label = Label(self, text="Spin", fg=FG_COLOR, bg=BG_COLOR, font="Arial 18 bold")
        self.spin_label.grid(column = 0, row = 4, sticky=(N,E,S,W))

class TelemetryStatus(Frame):
    SPACING = 30

    def set_name(self,
                 name: str):
        self.name.config(text = name)

    def update_value(self,
                     last_packet: int,
                     last_timestamp: float,
                     rssi: int) -> None:

        self.last_packet.config(text=f'#{last_packet}')
        self.last_timestamp.config(text=f'{last_timestamp:.2f}')
        self.rssi.config(text=f'{rssi:.0f} dB')

    def __init__(self, master):
        Frame.__init__(self, master, background=BG_COLOR)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.name = Label(self, text="", fg=FG_COLOR, bg=BG_COLOR, font="Arial 24")
        self.name.grid(column = 0, row = 0, sticky = (N,E,S,W), pady=(TelemetryStatus.SPACING,0))

        self.last_packet = Label(self, text="0", fg=FG_COLOR, bg=BG_COLOR, font="Arial 18")
        self.last_packet.grid(column = 0, row = 1, sticky = (N,E,S,W), pady=(TelemetryStatus.SPACING,0))

        self.last_packet_label = Label(self, text="Last Packet #", fg=FG_COLOR, bg=BG_COLOR, font="Arial 14 bold")
        self.last_packet_label.grid(column = 0, row = 2, sticky = (N,E,S,W))

        self.last_timestamp = Label(self, text="0", fg=FG_COLOR, bg=BG_COLOR, font="Arial 18")
        self.last_timestamp.grid(column = 0, row = 3, sticky = (N,E,S,W), pady=(TelemetryStatus.SPACING,0))

        self.last_timestamp_label = Label(self, text="Last Timestamp", fg=FG_COLOR, bg=BG_COLOR, font="Arial 14 bold")
        self.last_timestamp_label.grid(column = 0, row = 4, sticky = (N,E,S,W))

        self.rssi = Label(self, text="-inf dB", fg=FG_COLOR, bg=BG_COLOR, font="Arial 18")
        self.rssi.grid(column = 0, row = 5, sticky=(N,E,S,W), pady=(TelemetryStatus.SPACING,0))

        self.rssi_label = Label(self, text="RSSI", fg=FG_COLOR, bg=BG_COLOR, font="Arial 14 bold")
        self.rssi_label.grid(column = 0, row = 6, sticky=(N,E,S,W))

class TelemetryControls(Frame):
    SPACING = 30

    def update_value(self,
                    status_number: int) -> None:
        self.status_number.config(text=status_number)

    def __init__(self, master):
        Frame.__init__(self, master, background=BG_COLOR)

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.status_number = Label(self, text="0", fg=FG_COLOR, bg=BG_COLOR, font="Arial 72")
        self.status_number.grid(column = 0, row = 1, sticky = (N,E,S,W), pady=(TelemetryStatus.SPACING,0))
