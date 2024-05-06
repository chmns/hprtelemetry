from tkinter import *
from Styles import Fonts, Colors

DEFAULT_FORMAT = "{:.2f}"

LARGE_FONT_SIZE = 40
MEDIUM_FONT_SIZE = 24
SMALL_FONT_SIZE = 14

class ReadOut(Frame):
    def __init__(self,
                 master,
                 name: str,
                 variable: DoubleVar,
                 units: str = "",
                 color: str = Colors.FG_COLOR,
                 format: str = DEFAULT_FORMAT,):

        Frame.__init__(self, master, bg=Colors.BG_COLOR)

        self.variable = variable

        self.name = name
        self.min_var = StringVar(self, "0.0")
        self.min = 0.0
        self.max_var = StringVar(self,"0.0")
        self.max = 0.0
        self.value = StringVar(self, "0.0")
        self.units = units
        self.format = format
        self.color = color

        self.variable.trace_add("write", self.update_value)

        Frame(self, bg=Colors.BG_COLOR).pack(fill=BOTH, expand=True)

        self.main_label = Label(self, textvariable=self.value, fg=Colors.FG_COLOR, bg=Colors.BG_COLOR, font=("Arial", LARGE_FONT_SIZE))
        self.main_label.pack(fill=X)

        self.name_label = Label(self, text=self.name, fg=self.color, bg=Colors.BG_COLOR, font=("Arial", MEDIUM_FONT_SIZE))
        self.name_label.pack(fill=X)

        self.max_label = NumberLabel(self, textvariable=self.max_var, name="Max:", font=Fonts.SMALL_FONT, units=self.units)
        self.max_label.pack()
        self.min_label = NumberLabel(self, textvariable=self.min_var, name="Min:", font=Fonts.SMALL_FONT, units=self.units)
        self.min_label.pack()

        Frame(self, bg=Colors.BG_COLOR).pack(fill=BOTH, expand=True)

    def update_value(self, *_):
        new_value = self.variable.get()
        new_value_string = self.format.format(new_value)

        if new_value < self.min:
            self.min_var.set(new_value_string)

        if new_value > self.max:
            self.max_var.set(new_value_string)

        self.value.set(new_value_string)

    def reset(self):
        self.min_var.set(self.format.format(0))
        self.min = 0.0
        self.max_var.set(self.format.format(0))
        self.max = 0.0

class NumberLabel(Frame):
    def __init__(self, master, name: str, textvariable: Variable, units: str,
                 font: str = Fonts.MEDIUM_FONT_BOLD, fg: str = Colors.WHITE, bg: str = Colors.BLACK) -> None:

        super().__init__(master, bg=bg)

        self.name_label = Label(self, text=name, anchor=E, font=font, bg=Colors.BG_COLOR, fg=fg)
        self.name_label.pack(side=LEFT, expand=True, fill=X)

        self.value_label = Label(self, textvariable=textvariable, font=font, bg=Colors.BG_COLOR, fg=fg)
        self.value_label.pack(side=LEFT, expand=False, fill=None)

        self.units_label = Label(self, text=units, anchor=W, font=font, bg=Colors.BG_COLOR, fg=fg)
        self.units_label.pack(side=LEFT, expand=True, fill=X)