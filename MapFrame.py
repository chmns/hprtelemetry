from tkinter import *
import tkintermapview

class MapFrame(Frame):
    def __init__(self, master):
        Frame.__init__(self, master, bg="blue")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        map = tkintermapview.TkinterMapView(self)
        map.grid(row=0, column=0, sticky=(N,E,S,W))
        map.lat = 44.7916443
        map.lon = -0.5995578
        map.set_position(map.lat, map.lon)
        map.set_zoom(14)
        map.grid_propagate(True)

        location_grid = LocationGrid(self)
        location_grid.grid(row=1, column=0, sticky=(N,E,S,W))
        location_grid.grid_propagate(False)

class LocationGrid(Frame):
    def __init__(self, master):
        Frame.__init__(self, master, bg="green", height=110)

        self.pre = LocationRow(self, "PreLaunch:")
        self.pre.grid(row=0, column=0, sticky=(E,W))
        self.pre.grid_propagate(True)

        self.cur = LocationRow(self, "InFlight:")
        self.cur.grid(row=1, column=0, sticky=(E,W))
        self.cur.grid_propagate(True)

        self.post = LocationRow(self, "PostFlight:")
        self.post.grid(row=2, column=0, sticky=(E,W))
        self.post.grid_propagate(True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure((0, 1, 2), weight=0)

class LocationRow(Frame):
    def set_location(self, lat, lon, alt):
        self.lat.config(text=str(lat))
        self.lon.config(text=str(lon))
        self.alt.config(text=f"{str(alt)}m")
        pass

    def __init__(self,
                 master,
                 name,
                 font: str = "Courier 20 bold",
                 fg:  str = "#FFFFFF",
                 bg: str = "#0F0F0F"):

        Frame.__init__(self, master, bg=bg)

        self.name = Label(self, text=name, bg=bg, fg=fg, font=font, width=14, justify="right")
        self.name.grid(row=0, column=0, sticky=(N,S))

        self.lat = Label(self, text=f"-", bg=bg, fg=fg, font=font)
        self.lat.grid(row=0, column=1, sticky=(N,S))

        self.lon = Label(self, text=f"-", bg=bg, fg=fg, font=font)
        self.lon.grid(row=0, column=2, sticky=(N,S))

        self.alt = Label(self, text=f"0m", bg=bg, fg=fg, font=font)
        self.alt.grid(row=0, column=3, sticky=(N,S))

        self.columnconfigure(0, weight=0)
        self.columnconfigure((1,2,3), weight=1)
