from tkinter import *
import tkintermapview

DEFAULT_LAT = 44.7916443
DEFAULT_LON = -0.5995578
DEFAULT_ZOOM = 14


class MapFrame(Frame):

    def update(self):
        new_lat = self.lat_var.get()
        new_lon = self.lon_var.get()
        new_alt = self.alt_var.get()

        if new_lat != self.lat or new_lon != self.lon:
            self.lat = new_lat
            self.lon = new_lon
            self.map_view.set_position(self.lat, self.lon, marker=True)
            self.location_grid.current.set_location(self.lat, self.lon, new_alt)

    def reset(self):
        self.lat = DEFAULT_LAT
        self.lon = DEFAULT_LON
        self.map_view.set_position(self.lat, self.lon)
        self.map_view.set_zoom(DEFAULT_ZOOM)

    def __init__(self, master, lat_var_name, lon_var_name, alt_var_name):
        Frame.__init__(self, master, bg="blue")

        self.lat_var = DoubleVar(master, 0.0, lat_var_name)
        self.lon_var = DoubleVar(master, 0.0, lon_var_name)
        self.alt_var = DoubleVar(master, 0.0, alt_var_name)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        self.map_view = tkintermapview.TkinterMapView(self)
        self.map_view.grid(row=0, column=0, sticky=(N,E,S,W))
        self.map_view.grid_propagate(True)

        self.location_grid = LocationGrid(self)
        self.location_grid.grid(row=1, column=0, sticky=(N,E,S,W))
        self.location_grid.grid_propagate(False)
        self.reset()

class LocationGrid(Frame):
    def __init__(self, master):
        Frame.__init__(self, master, bg="green", height=110)

        self.pre = LocationRow(self, "PreLaunch:")
        self.pre.grid(row=0, column=0, sticky=(E,W))
        self.pre.grid_propagate(True)

        self.current = LocationRow(self, "InFlight:")
        self.current.grid(row=1, column=0, sticky=(E,W))
        self.current.grid_propagate(True)

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
