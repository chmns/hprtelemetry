from tkinter import *
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from collections import deque
from Styles import Colors

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

    def update_data(self):
        new_y = self.yvars[0].get()

        # if new_y > self.max:
        #     self.max = new_y

        # if new_y < self.min:
        #     self.min = new_y

        self.ys.append(new_y)

    def __init__(self, master, **kwargs):
        Frame.__init__(self, master, **kwargs)

        self.yvars = [DoubleVar(master, 0.0, "fusionAlt"),
                      DoubleVar(master, 0.0, "velocity"),
                      DoubleVar(master, 0.0, "acceleration")]

        self.ranges = [(-10,+1000), # Alt
                       (-20,+20),   # Vel
                       (-30,+30)]   # Acc

        self.__zero_data__()

        # plt.tight_layout()
        self.figure, self.ax = plt.subplots() #(3, sharex=True)
        (self.line,) = self.ax.plot(self.xs, self.ys, animated=True)

        # self.acc, = self.acc_ax.plot(self.xs, self.ys, Colors.ACCELERATION_COLOR, linewidth=LINEWIDTH)
        # self.vel, = self.vel_ax.plot(self.xs, self.ys, Colors.VELOCITY_COLOR, linewidth=LINEWIDTH)
        # self.alt, = self.alt_ax.plot(self.xs, self.ys, Colors.ALTITUDE_COLOR, linewidth=LINEWIDTH)


        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)

        self.canvas.draw()
        self.blit_manager = BlitManager(self.canvas, [self.line])

    def draw(self):
        self.line.set_ydata(self.ys)
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