from tkinter import *
from tkintermapview import TkinterMapView, OfflineLoader
from tkintermapview.utility_functions import osm_to_decimal
import os # for maps db

DEFAULT_LAT = 44.7916443
DEFAULT_LON = -0.5995578
DEFAULT_ZOOM = 14
ZOOM_RANGE = 2 # range of zoom levels to
MIN_PATH_POINTS = 2

START_TEXT = "Start"
LAUNCH_TEXT = "Landing"
LANDING_TEXT = "Launch"
DEFAULT_DATABASE_NAME = "offline_tiles.db"
TILE_SERVER_URL = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"

class MapFrame(Frame):

    def update(self):
        new_lat = self.lat_var.get()
        new_lon = self.lon_var.get()

        # print(f"{new_lat = } : {new_lon =}")

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
        top_left_position = osm_to_decimal(*self.map_view.upper_left_tile_pos, current_zoom)
        bottom_right_position = osm_to_decimal(*self.map_view.lower_right_tile_pos, current_zoom)
        zoom_min = 0
        zoom_max = 14

        print(f"Attempting to download region bound by: {top_left_position} and {bottom_right_position}")
        print(f"Zoom level: {self.map_view.zoom}")

        self.map_view.set_position(*top_left_position)

        self.downloader.save_offline_tiles(top_left_position,
                                           bottom_right_position,
                                           zoom_min,
                                           zoom_max)

        pass

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
        Frame.__init__(self, master, bg="blue")

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

        self.map_view.grid(row=0, column=0, sticky=(N,E,S,W))
        self.map_view.grid_propagate(True)

        self.location_grid = LocationGrid(self)
        self.location_grid.grid(row=1, column=0, sticky=(N,E,S,W))
        self.location_grid.grid_propagate(False)

        self.reset()

class LocationGrid(Frame):
    def __init__(self, master):
        Frame.__init__(self, master, bg="green", height=110)

        self.pre = LocationRow(self,
                               "Launch:",
                               DoubleVar(master, "0.0", "launch_latitude"),
                               DoubleVar(master, "0.0", "launch_longitude"),
                               DoubleVar(master, "0.0", "launch_altitude"))
        self.pre.grid(row=0, column=0, sticky=(E,W))
        self.pre.grid_propagate(True)

        self.current = LocationRow(self,
                                   "Current:",
                                   DoubleVar(master, "0.0", "gnssLat"),
                                   DoubleVar(master, "0.0", "gnssLon"),
                                   DoubleVar(master, "0.0", "gnssAlt"))
        self.current.grid(row=1, column=0, sticky=(E,W))
        self.current.grid_propagate(True)

        self.post = LocationRow(self,
                                   "Landing:",
                                   StringVar(master, "0.0", "landing_latitude"),
                                   StringVar(master, "0.0", "landing_longitude"),
                                   StringVar(master, "0.0", "landing_altitude"))
        self.post.grid(row=2, column=0, sticky=(E,W))
        self.post.grid_propagate(True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure((0, 1, 2), weight=0)

class LocationRow(Frame):
    def __init__(self,
                 master,
                 name,
                 lat_var,
                 lon_var,
                 alt_time_var,
                 font: str = "Courier 20 bold",
                 fg:  str = "#FFFFFF",
                 bg: str = "#0F0F0F"):

        Frame.__init__(self, master, bg=bg)

        self.name = Label(self, text=name, bg=bg, fg=fg, font=font, width=14, justify="right")
        self.name.grid(row=0, column=0, sticky=(N,S))

        self.lat = Label(self, textvariable=lat_var, bg=bg, fg=fg, font=font)
        self.lat.grid(row=0, column=1, sticky=(N,S))

        self.lon = Label(self, textvariable=lon_var, bg=bg, fg=fg, font=font)
        self.lon.grid(row=0, column=2, sticky=(N,S))

        self.alt = Label(self, textvariable=alt_time_var, bg=bg, fg=fg, font=font)
        self.alt.grid(row=0, column=3, sticky=(N,S))

        self.columnconfigure(0, weight=0)
        self.columnconfigure((1,2,3), weight=1)
