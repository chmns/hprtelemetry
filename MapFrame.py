from tkinter import *
from tkintermapview import TkinterMapView, OfflineLoader
from tkintermapview.utility_functions import osm_to_decimal
from Styles import Fonts
import os # for maps db

DEFAULT_LAT = 44.7916443
DEFAULT_LON = -0.5995578
OFFLINE_ZOOM_MIN = 0
OFFLINE_ZOOM_MAX = 14
MIN_PATH_POINTS = 2
DEFAULT_ZOOM = 10

START_TEXT = "Start"
LAUNCH_TEXT = "Landing"
LANDING_TEXT = "Launch"

PRELIGHT_TEXT =   " Pre:"
CURRENT_TEXT =    " Now:"
POSTFLIGHT_TEXT = "Post:"

ZERO_LAT = "0.000000"
ZERO_LON = "0.000000"
ZERO_ALT = "0"

PADX = 4
PADY = 4

DEFAULT_DATABASE_NAME = "offline_tiles.db"
TILE_SERVER_URL = "http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga"

class MapFrame(Frame):

    def update(self):
        new_lat = self.lat_var.get()
        new_lon = self.lon_var.get()

        if new_lat != self.lat or new_lon != self.lon:
            self.lat = new_lat
            self.lon = new_lon
            self.map_view.set_position(new_lat, new_lon)

            # hacky way to do it but can't get the method in documentation
            # working. need to have at least 2 points before creating path
            # and then after that you append to it, rather than setting it
            if self.path is None:
                if len(self.path_list) > MIN_PATH_POINTS:
                    self.start_marker = self.map_view.set_marker(new_lat, new_lon, START_TEXT)
                    self.path = self.map_view.set_path(self.path_list)
                else:
                    self.path_list.append((new_lat, new_lon))
            else:
                self.path.add_position(new_lat, new_lon)

    def set_landing_point(self, landing_lat, landing_lon):
        self.landing_marker = self.map_view.set_marker(landing_lat, landing_lon, LANDING_TEXT)

    def set_launch_point(self, launch_lat, launch_lon):
        self.launch_marker = self.map_view.set_marker(launch_lat, launch_lon, LAUNCH_TEXT)

    def reset(self):
        self.location_grid.reset()
        self.lat = DEFAULT_LAT
        self.lon = DEFAULT_LON
        self.map_view.set_position(self.lat, self.lon)
        self.map_view.set_zoom(DEFAULT_ZOOM)
        self.map_view.delete_all_path()
        self.path_list = []
        self.path = None
        self.map_view.delete_all_marker()
        self.start_marker = None
        self.landing_marker = None
        self.launch_marker = None

    def download_current_map(self):

        current_zoom = self.map_view.zoom
        current_position = self.map_view.get_position()
        top_left_position = osm_to_decimal(*self.map_view.upper_left_tile_pos, current_zoom)
        bottom_right_position = osm_to_decimal(*self.map_view.lower_right_tile_pos, current_zoom)

        print(f"Attempting to download region bound by: {top_left_position} and {bottom_right_position}")
        print(f"Zoom level: {self.map_view.zoom}")

        self.map_view.set_position(*top_left_position)

        try:
            self.downloader.save_offline_tiles(top_left_position,
                                               bottom_right_position,
                                               OFFLINE_ZOOM_MIN,
                                               OFFLINE_ZOOM_MAX)
        except Exception:
            print("Error downloading offline maps")
        else:
            self.map_view.set_position(*current_position)

    def set_only_offline_maps(self, only_offline):
        self.map_view.use_database_only = only_offline

        # hack to get maps to start loading when online is re-enabled
        if not only_offline:
            current_zoom = self.map_view.zoom
            self.map_view.set_zoom(current_zoom+1)
            self.map_view.set_zoom(current_zoom)

    def load_offline_database(self, database_path):
        print(f"Setting offline map file to: {database_path}")

        self.map_view = TkinterMapView(self, database_path = database_path)
        self.map_view.grid(row=0, column=0, sticky=(N,E,S,W))
        self.map_view.grid_propagate(True)

    def __init__(self, master, lat_var, lon_var, alt_var, offline_maps_only_var):
        Frame.__init__(self, master)

        self.lat_var = lat_var
        self.lon_var = lon_var
        self.alt_var = alt_var

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        script_directory = os.path.dirname(os.path.abspath(__file__))
        self.database_path = os.path.join(script_directory, DEFAULT_DATABASE_NAME)

        self.downloader = OfflineLoader(path=self.database_path,
                                        tile_server=TILE_SERVER_URL)

        print(f"Online maps downloading enabled?: {offline_maps_only_var.get()}")
        print(f"Using offline maps database at: {self.database_path}")

        self.map_view = TkinterMapView(self,
                                       database_path=self.database_path,
                                       use_database_only=offline_maps_only_var.get())
        self.map_view.set_tile_server(TILE_SERVER_URL)

        self.map_view.grid(row=0, column=0, sticky=(N,E,S,W))
        self.map_view.grid_propagate(True)

        self.location_grid = LocationGrid(self)
        self.location_grid.grid(row=1, column=0, sticky=(N,E,S,W))
        self.location_grid.grid_propagate(True)

        self.reset()

class LocationGrid(Frame):
    def __init__(self, master):
        Frame.__init__(self, master, bg="black")

        self.preLatitude   = StringVar(master, ZERO_LAT, "preGnssLat")
        self.preLongitude  = StringVar(master, ZERO_LON, "preGnssLon")
        self.preAltitude   = StringVar(master, ZERO_ALT, "preGnssAlt")
        self.curLatitude   = StringVar(master, DEFAULT_LAT, "gnssLat")
        self.curLongitude  = StringVar(master, DEFAULT_LON, "gnssLon")
        self.curAltitude   = StringVar(master, ZERO_ALT, "gnssAlt")
        self.postLatitude  = StringVar(master, ZERO_LAT, "postGnssLat")
        self.postLongitude = StringVar(master, ZERO_LON, "postGnssLon")
        self.postAltitude  = StringVar(master, ZERO_ALT, "postGnssAlt")


        self.pre = LocationRow(self,
                               PRELIGHT_TEXT,
                               self.preLatitude,
                               self.preLongitude,
                               self.preAltitude)
        self.pre.grid(row=0, column=0, sticky=(E,W))
        self.pre.grid_propagate(True)

        self.current = LocationRow(self,
                                   CURRENT_TEXT,
                                   self.curLatitude,
                                   self.curLongitude,
                                   self.curAltitude)
        self.current.grid(row=1, column=0, sticky=(E,W), pady=PADY)
        self.current.grid_propagate(True)

        self.post = LocationRow(self,
                                POSTFLIGHT_TEXT,
                                self.postLatitude,
                                self.postLongitude,
                                self.postAltitude)
        self.post.grid(row=2, column=0, sticky=(E,W))
        self.post.grid_propagate(True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure((0, 1, 2), weight=0)

        self.preLatitude.trace_add("write", lambda *_ : self.pre.grid())
        self.curLatitude.trace_add("write", lambda *_ : self.current.grid())
        self.postLatitude.trace_add("write", lambda *_ : self.post.grid())


    def reset(self):
        self.preLatitude.set(ZERO_LAT)
        self.preLongitude.set(ZERO_LON)
        self.preAltitude.set(ZERO_ALT)

        self.curLatitude.set(DEFAULT_LAT)
        self.curLongitude.set(DEFAULT_LON)
        self.curAltitude.set(ZERO_ALT)

        self.postLatitude.set(ZERO_LAT)
        self.postLongitude.set(ZERO_LON)
        self.postAltitude.set(ZERO_ALT)

        self.pre.grid_remove()
        self.current.grid_remove()
        self.post.grid_remove()

class LocationRow(Frame):
    def __init__(self,
                 master,
                 name,
                 lat_var,
                 lon_var,
                 alt_time_var,
                 fg:  str = "#FFFFFF",
                 bg: str = "#0F0F0F"):

        Frame.__init__(self, master, bg=bg)

        self.name = Label(self, text=name, width=6, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="right")
        self.name.grid(row=0, column=0, sticky=(N,S), padx=PADX, pady=PADY)

        self.lat = Label(self, textvariable=lat_var, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="center")
        self.lat.grid(row=0, column=1, sticky=(N,E,W,S), padx=PADX, pady=PADY)

        self.lon = Label(self, textvariable=lon_var, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="center")
        self.lon.grid(row=0, column=2, sticky=(N,E,W,S), padx=PADX, pady=PADY)

        self.alt = Label(self, width=5, textvariable=alt_time_var, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="center")
        self.alt.grid(row=0, column=3, sticky=(N,S), padx=PADX, pady=PADY)

        self.columnconfigure((0,3), weight=0)
        self.columnconfigure((1,2), weight=1, uniform="b")
