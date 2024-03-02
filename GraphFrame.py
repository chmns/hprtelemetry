from tkinter import *
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from collections import deque

NUM_POINTS = 200
LINEWIDTH = 1.5
TIMEBASE = 0.05
BG_COLOR = "#0f0f0f"
FG_COLOR = "#eeeeee"

class GraphFrame(Frame):

    def reset(self):
        self.__zero_data__()
        self.canvas.draw()

    def update(self):
        self.xs.append(self.appended)

        new_values = [var.get() for var in self.variables]
        for (value, y) in zip(new_values, self.ys):
            if value > self.max:
                self.max = value
            if value < self.min:
                self.min = value
            y.append(value)


    def __zero_data__(self):
        self.xs = [x * TIMEBASE for x in (range(0 - NUM_POINTS,0))]
        self.ys = len(self.variables) * deque([], maxlen=NUM_POINTS)

    def __init__(self,
                 master,
                 units: str,
                 color: str = "black",
                 y_range: tuple = None,
                 elapsed_var_name: str = "elapsed",
                 *y_axis_var_names: str) -> None:

        Frame.__init__(self, master, bg=BG_COLOR)

        self.master = master
        self.units = units
        self.color = color
        self.max = 0
        self.min = 0
        self.y_range = y_range

        self.last_time = 0
        self.time = IntVar(master, 0, elapsed_var_name)

        self.variables = [DoubleVar(master, 0.0, var_name) for var_name in y_axis_var_names]

        plt.tight_layout()
        self.relief = RAISED
        self.borderwidth = 2

        self.figure = Figure(figsize=(4,4), dpi=200)
        self.subplot = self.figure.add_subplot()
        self.subplot.set_autoscaley_on(True)
        self.subplot.grid("True")

        self.ani = animation.FuncAnimation(self.fig,
                                           self.update_graph,
                                           interval=int(self.interval.get()),
                                           repeat=False)

        self.__zero_data__()

        self.lines = list()
        for y in self.ys:
            line, = self.subplot.plot(self.xs, y, self.color, linewidth=LINEWIDTH)
            self.lines.append(line)

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