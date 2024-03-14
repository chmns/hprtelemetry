from tkinter import *
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from collections import deque

NUM_POINTS = 400 # @ 10ms accuracy this is about 4seconds
LINEWIDTH = 1
FPS = 20 # update rate of graph
INTERVAL = 0.01 # message resolution is approx. 10ms
BG_COLOR = "#0f0f0f"
FG_COLOR = "#eeeeee"

class GraphFrame(Frame):

    def reset(self):
        self.__zero_data__()
        self.canvas.draw()

    def start(self):
        """
        called to start the animated re-drawing of graph
        when telemetry data begins to arrive
        """
        pass

    def stop(self):
        """
        called at the end of a sequence of messages to end
        graph animation
        """
        pass

    def update(self):
        """
        called by the main app when new message data arrives
        new points are added to local cache
        actual drawing is called asynchronously by animator
        """
        self.xs.append(self.appended)

        # new_values = [var.get() for var in self.variables]
        # for (value, y) in zip(new_values, self.ys):
        #     if value > self.max:
        #         self.max = value
        #     if value < self.min:
        #         self.min = value
        #     y.append(value)
        new_value = self.variables[0].get()
        self.ys.append(new_value)


    def __zero_data__(self):
        # self.xs = [x * INTERVAL for x in (range(0 - NUM_POINTS,0))]
        self.xs = deque(range(0-NUM_POINTS, 0), maxlen=NUM_POINTS)
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
        self.subplot = self.figure.add_subplot() # 'ax'
        self.subplot.set_autoscaley_on(True)
        self.subplot.grid("True")

        self.__zero_data__()

        self.lines = list()
        for y in self.ys:
            line, = self.subplot.plot(self.xs, y, self.color, linewidth=LINEWIDTH)
            self.lines.append(line)

        if self.y_range is not None:
            self.subplot.set_ylim(*self.y_range)

        self.subplot.set_xlim(NUM_POINTS)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)
        self.canvas.draw()

    def draw(self):
        for (line, y) in zip(self.lines, self.ys):
            line.set_data(self.xs, y)

        self.line.set_ydata(self.ys)

        if self.y_range is None:
            self.subplot.set_ylim(self.min, self.max)

        self.canvas.draw()