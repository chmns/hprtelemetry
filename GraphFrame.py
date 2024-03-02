from tkinter import *
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

NUM_POINTS = 200
LINEWIDTH = 1.5
TIMEBASE = 0.05
BG_COLOR = "#0f0f0f"
FG_COLOR = "#eeeeee"

class GraphFrame(Frame):

    def reset(self):
        self.__zero_data__()
        self.canvas.draw()

    def append(self, value):
        if value > self.max:
            self.max = value

        if value < self.min:
            self.min = value

        if self.appended < NUM_POINTS:
            self.ys.pop(0)
            self.xs.pop(0)

        self.ys.append(value)
        self.xs.append(self.appended * TIMEBASE)

        self.draw()
        self.appended += 1

    def __zero_data__(self):
        self.ys = NUM_POINTS*[0]
        self.xs = [x * TIMEBASE for x in (range(0-NUM_POINTS,0))]

    def __init__(self,
                 master,
                 units: str,
                 color: str = "black",
                 y_range: tuple = None,
                 time_var_name: str = "time",
                 *y_axis_var_names: str) -> None:

        Frame.__init__(self, master, bg=BG_COLOR)

        self.master = master
        self.units = units
        self.color = color
        self.max = 0
        self.min = 0
        self.appended = 0
        self.y_range = y_range

        self.last_time = 0
        self.time = IntVar(master, 0, time_var_name)

        self.variables = [DoubleVar(master, 0.0, var_name) for var_name in y_axis_var_names]

        plt.tight_layout()
        self.relief = RAISED
        self.borderwidth = 2

        self.figure = Figure(figsize=(4,4), dpi=200)
        self.subplot = self.figure.add_subplot()
        self.subplot.set_autoscaley_on(True)
        self.subplot.grid("True")

        self.__zero_data__()
        self.line, = self.subplot.plot(self.xs, self.ys, self.color, linewidth=LINEWIDTH)

        if self.y_range is not None:
            self.subplot.set_ylim(*self.y_range)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)
        self.canvas.draw()


    def draw(self):
        self.line.set_xdata(self.xs)
        self.subplot.set_xlim(self.xs[0],
                              self.xs[len(self.xs)-1])

        self.line.set_ydata(self.ys)

        if self.y_range is None and self.appended > 0:
            self.subplot.set_ylim(self.min, self.max)