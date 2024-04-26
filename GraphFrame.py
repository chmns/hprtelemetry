from tkinter import *
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from collections import deque

NUM_POINTS = 1000
LINEWIDTH = 1
FPS = 20 # update rate of graph
INITIAL_INTERVAL = 1 # for filling empty space at start
BG_COLOR = "#0f0f0f"
FG_COLOR = "#eeeeee"

class GraphFrame(Frame):

    def __zero_data__(self):
        self.ys = deque(NUM_POINTS*[0], NUM_POINTS)
        self.xs = [x * INITIAL_INTERVAL for x in (range(0-NUM_POINTS,0))]

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
        new_y = self.y_var.get()
        new_x = self.x_var.get()

        if new_y > self.max:
            self.max = new_y

        if new_y < self.min:
            self.min = new_y

        self.ys.append(new_y)


    def render(self):
        self.draw()

    def __init__(self,
                 master,
                 units: str,
                 x_var: DoubleVar,
                 y_var: DoubleVar,
                 y_range: tuple = None,
                 color: str = "black"):

        Frame.__init__(self, master, bg=BG_COLOR)

        self.master = master
        self.units = units
        self.color = color
        self.max = 0
        self.min = 0
        self.appended = 0
        self.y_range = y_range
        self.x_var = x_var
        self.y_var = y_var

        plt.tight_layout()
        self.relief = RAISED
        self.borderwidth = 2

        self.figure = Figure(figsize=(4,4), dpi=150, constrained_layout=True)
        self.subplot = self.figure.add_subplot()
        self.subplot.set_autoscaley_on(True)

        self.__zero_data__()

        self.subplot.set_ylabel(units)
        self.subplot.grid("True")

        self.line, = self.subplot.plot(self.xs, self.ys, self.color, linewidth=LINEWIDTH)

        if self.y_range is not None:
            self.subplot.set_ylim(*self.y_range)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)
        self.canvas.draw()

    def draw(self):
        self.line.set_xdata(self.xs)
        # self.subplot.set_xlim(self.xs[0],
        #                       self.xs[len(self.xs)-1])

        self.line.set_ydata(self.ys)

        self.subplot.set_ylim(self.min, self.max)

        self.canvas.draw()
        self.canvas.flush_events()

