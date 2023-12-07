from tkinter import *
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import numpy as np

EXAMPLE_POINTS = 100

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

class GraphFrame(Frame):

    def __init__(self,
                 master,
                 units: str,
                 color: str = "black"):
        
        Frame.__init__(self, master)   

        self.master = master
        self.units = units
        self.color = color

        plt.tight_layout() 
        self.relief = RAISED
        self.borderwidth = 2
        
        figure = Figure(figsize=(4,4), dpi=200)
        subplot = figure.add_subplot()
        
        scale = np.random.normal(1,2,1)[0]**2
        ys = moving_average(np.random.normal(1,scale,EXAMPLE_POINTS), round(10+scale*3)).tolist()
        xs = list(range(len(ys)))

        subplot.set_ylabel(units)
        subplot.grid("True")
      
        subplot.plot(xs,ys, self.color, linewidth=3)

        canvas = FigureCanvasTkAgg(figure, self)
        canvas.get_tk_widget().pack(side=BOTTOM, fill=BOTH, expand=True)
        canvas.draw()
