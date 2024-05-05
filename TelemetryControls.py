from tkinter import *
from Styles import Fonts, Colors

BG_COLOR = "#0f0f0f"
FG_COLOR = "#eeeeee"

NAME_TEXT_WRAPLENGTH = 160

LARGE_FONT_SIZE = 40
MEDIUM_FONT_SIZE = 24
SMALL_FONT_SIZE = 14

class ReadOut(Frame):
    def __init__(self,
                 master,
                 name: str,
                 variable: Variable,
                 units: str,
                 color: str = FG_COLOR):

        Frame.__init__(self, master, bg=BG_COLOR)

        self.variable = variable

        self.name = name
        self.value = 0
        self.min = IntVar(self, 0.0, "min")
        self.max = IntVar(self, 0.0, "max")
        self.units = units
        self.color = color

        self.variable.trace_add("write", self.update_value)

        Frame(self, bg=BG_COLOR).pack(fill=BOTH, expand=True)

        self.main = Label(self, textvariable=variable, fg=FG_COLOR, bg=BG_COLOR, font=("Arial", LARGE_FONT_SIZE))
        self.main.pack(fill=X)

        self.name = Label(self, text=f'{self.name}', fg=self.color, bg=BG_COLOR, font=("Arial", MEDIUM_FONT_SIZE))
        self.name.pack(fill=X)

        self.max_label = NumberLabel(self, textvariable=self.max, name="Max:", font=Fonts.SMALL_FONT, units=self.units)
        self.max_label.pack()
        self.min_label = NumberLabel(self, textvariable=self.min, name="Min:", font=Fonts.SMALL_FONT, units=self.units)
        self.min_label.pack()

        Frame(self, bg=BG_COLOR).pack(fill=BOTH, expand=True)

    def update_value(self, *_):
        new_value = self.variable.get()

        if new_value >= self.min.get():
            self.min.set(new_value)

        if new_value >= self.max.get():
            self.max.set(new_value)

    def reset(self):
        self.min.set(0)
        self.max.set(0)

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