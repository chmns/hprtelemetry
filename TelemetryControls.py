from tkinter import *
from Styles import Fonts

BG_COLOR = "#0f0f0f"
FG_COLOR = "#eeeeee"

NAME_TEXT_WRAPLENGTH = 160

LARGE_FONT_SIZE = 40
MEDIUM_FONT_SIZE = 24
SMALL_FONT_SIZE = 14

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

        self.main = Label(self, text="0", fg=FG_COLOR, bg=BG_COLOR, font=("Arial", LARGE_FONT_SIZE))
        self.main.grid(column = 0, row = 1, sticky = (N,S))

        self.name = Label(self, text=f'{self.name}', fg=self.color, bg=BG_COLOR, font=("Arial", MEDIUM_FONT_SIZE))
        self.name.grid(column = 0, row = 2, sticky=(N,S))

        self.max = Label(self, text=f'Max:\n{self.max_value}{units1}', fg=FG_COLOR, bg=BG_COLOR, font=("Arial", SMALL_FONT_SIZE))
        self.max.grid(column = 0, row = 4, sticky=(N,S))

        self.final = Label(self, text="", fg=self.color, bg=BG_COLOR, font=("Arial Bold", SMALL_FONT_SIZE))
        self.final.grid(column = 0, row = 6, sticky=(N,S))


class TelemetryStatus(Frame):
    def __init__(self,
                 master,
                 packet_num_var_name: str,
                 time_var_name: str,
                 num_sats_var_name: str):

        Frame.__init__(self, master, background=BG_COLOR)

        self.last_packet = Label(self, textvariable=IntVar(master, 0, packet_num_var_name), fg=FG_COLOR, bg=BG_COLOR, font=Fonts.MEDIUM_FONT)
        self.last_packet.pack()

        self.last_packet_label = Label(self, text="Last Packet #", fg=FG_COLOR, bg=BG_COLOR, font=Fonts.MEDIUM_FONT)
        self.last_packet_label.pack()

        self.last_timestamp = Label(self, textvariable=IntVar(master, 0, time_var_name), fg=FG_COLOR, bg=BG_COLOR, font="Courier 18 bold")
        self.last_timestamp.pack()

        self.last_timestamp_label = Label(self, text="Last Timestamp", fg=FG_COLOR, bg=BG_COLOR, font="Arial 14 bold")
        self.last_timestamp_label.pack()

        self.num_sats = Label(self, textvariable=IntVar(master, 0, num_sats_var_name), fg=FG_COLOR, bg=BG_COLOR, font="Arial 18")
        self.num_sats.pack()

        self.num_sats_label = Label(self, text="# satellites", fg=FG_COLOR, bg=BG_COLOR, font="Arial 14 bold")
        self.num_sats_label.pack()
