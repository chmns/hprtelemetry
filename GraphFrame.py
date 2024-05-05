from tkinter import *
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from collections import deque
from Styles import Colors

NUM_GRAPHS = 3
NUM_POINTS = 1000
LINEWIDTH = 1
FPS = 20 # update rate of graph
INITIAL_INTERVAL = 1 # for filling empty space at start
BG_COLOR = "#0f0f0f"
FG_COLOR = "#eeeeee"
AXIS_NAMES = ["Altitude (m)", "Velocity (m/s)", "Acceleration (m/s/s)"]
LINE_COLORS = [Colors.ALTITUDE_COLOR, Colors.VELOCITY_COLOR, Colors.ACCELERATION_COLOR]

class GraphFrame(Frame):
    def reset_data(self):
        self.ys = []

        for _ in range(NUM_GRAPHS):
            self.ys.append(deque(NUM_POINTS*[0], NUM_POINTS))

        self.xs = [x * INITIAL_INTERVAL for x in (range(0-NUM_POINTS,0))]

        self.ranges = [(-100,+1000), # Alt
                       (-10,+100), # Vel
                       (-10,+10)] # Acc

    def reset(self):
        self.reset_data()
        self.canvas.draw()


    def update_data(self):
        changed = False

        for i in range(3):
            new_y = self.yvars[i].get()

            (min, max) = self.ranges[i]
            if new_y >= max:
                max += self.extend_size[i]
                changed = True
            elif new_y <= min:
                min -= self.extend_size[i]
                changed = True

            if changed:
                self.ranges[i] = (min,max)
                self.ax[i].set_ylim(self.ranges[i])

            self.ys[i].append(new_y)

        if changed:
            # do complete redraw for axes
            self.canvas.draw()


    def __init__(self, master, **kwargs):
        Frame.__init__(self, master, **kwargs)

        self.yvars = [DoubleVar(master, 0.0, "fusionAlt"),
                      DoubleVar(master, 0.0, "fusionVel"),
                      DoubleVar(master, 0.0, "accelZ")]

        self.extend_size = [1000, # alt
                            100,   # vel
                            100]   # accelz

        self.reset_data()

        self.figure, self.ax = plt.subplots(3, sharex=True)

        self.lines = []

        plt.subplots_adjust(bottom=0.075, right=0.95, top=0.95, left=0.15, hspace=0.1)
        plt.xlabel("Packet history")

        for i in range(NUM_GRAPHS):
            self.ax[i].set_ylim(self.ranges[i])
            self.ax[i].grid(color=Colors.GRAY)
            self.ax[i].set_ylabel(AXIS_NAMES[i])
            (line,) = self.ax[i].plot(self.xs, self.ys[i], LINE_COLORS[i], animated=True, linewidth=LINEWIDTH)
            self.lines.append(line)

        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)

        self.canvas.draw()
        self.blit_manager = BlitManager(self.canvas, self.lines)

    def draw(self):
        for i in range(NUM_GRAPHS):
            self.lines[i].set_ydata(self.ys[i])

        self.blit_manager.update()


class BlitManager:
    def __init__(self, canvas, animated_artists=()):
        """
        Parameters
        ----------
        canvas : FigureCanvasAgg
            The canvas to work with, this only works for subclasses of the Agg
            canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
            `~FigureCanvasAgg.restore_region` methods.

        animated_artists : Iterable[Artist]
            List of the artists to manage
        """
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)
        # grab the background on every draw
        self.cid = canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""
        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def add_artist(self, art):
        """
        Add an artist to be managed.

        Parameters
        ----------
        art : Artist

            The artist to be added.  Will be set to 'animated' (just
            to be safe).  *art* must be in the figure associated with
            the canvas this class is managing.

        """
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def _draw_animated(self):
        """Draw all of the animated artists."""
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        """Update the screen with animated artists."""
        cv = self.canvas
        fig = cv.figure
        # paranoia in case we missed the draw event,
        if self._bg is None:
            self.on_draw(None)
        else:
            # restore the background
            cv.restore_region(self._bg)
            # draw all of the animated artists
            self._draw_animated()
            # update the GUI state
            cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()