from tkinter import *
from tkintermapview import TkinterMapView, OfflineLoader
from tkintermapview.utility_functions import osm_to_decimal
from Styles import Fonts, Colors
from TelemetryDecoder import DecoderState
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


class MapColumn(PanedWindow):
    def __init__(self, master):
        PanedWindow.__init__(self, orient="vertical", background=Colors.BLACK)

        self.bytes_read = IntVar(master, 0, "bytes_read")
        self.event_name = StringVar(master, "", "eventName")
        self.name = StringVar(master, "", "name")
        self.callsign = StringVar(master, "", "callsign")
        self.telemetry_state_name = StringVar(master, "", "telemetryStateName")
        self.cont_name = StringVar(master, "", "contName")
        self.offline_maps_only = BooleanVar(master, True, "offline_maps_only")

        self.name_callsign_state_frame = Frame(self, bg=Colors.BG_COLOR)
        self.name_callsign_state_frame.pack(side=TOP, expand=False, fill=X, padx=PADX, pady=PADY)

        self.telemetry_state_label = Label(self.name_callsign_state_frame, textvariable=self.telemetry_state_name, font=Fonts.MEDIUM_FONT, bg=Colors.BG_COLOR, fg=Colors.LIGHT_GRAY)
        self.telemetry_state_label.pack(side=LEFT, expand=False, fill=NONE, padx=PADX)

        self.name_label = Label(self.name_callsign_state_frame, textvariable=self.name, font=Fonts.MEDIUM_FONT_BOLD, bg=Colors.BG_COLOR, fg=Colors.WHITE)
        self.name_label.pack(side=LEFT, expand=True, fill=X)

        self.callsign_label = Label(self.name_callsign_state_frame, textvariable=self.callsign, font=Fonts.MEDIUM_FONT_BOLD, bg=Colors.BG_COLOR, fg=Colors.WHITE)


        self.cont_event_frame = Frame(self, bg=Colors.BG_COLOR)
        self.cont_event_frame.pack(side=TOP, expand=False, fill=X, padx=PADX, pady=PADY)

        self.cont_label = Label(self.cont_event_frame, textvariable=self.cont_name, font=Fonts.MEDIUM_FONT, bg=Colors.BG_COLOR, fg=Colors.WHITE)

        self.event_name_label = Label(self.cont_event_frame, textvariable=self.event_name, font=Fonts.MEDIUM_FONT_BOLD, bg=Colors.BG_COLOR, fg=Colors.WHITE)
        self.event_name_label.pack(side=LEFT, expand=True, fill=X, padx=PADX)


        self.map_frame = MapFrame(self,
                                  DoubleVar(master, 0.0, "gnssLat"),
                                  DoubleVar(master, 0.0, "gnssLon"),
                                  DoubleVar(master, 0.0, "gnssAlt"),
                                  self.offline_maps_only)
        self.map_frame.pack(side=TOP, expand=True, fill=BOTH)


        self.preflight_location = LocationRow(self,
                                              PRELIGHT_TEXT,
                                              StringVar(master, ZERO_LAT, "preGnssLat"),
                                              StringVar(master, ZERO_LON, "preGnssLon"),
                                              StringVar(master, ZERO_ALT, "preGnssAlt"))

        self.current_location = LocationRow(self,
                                            CURRENT_TEXT,
                                            StringVar(master, ZERO_LAT, "gnssLat"),
                                            StringVar(master, ZERO_LON, "gnssLon"),
                                            StringVar(master, ZERO_ALT, "gnssAlt"))

        self.postflight_location = LocationRow(self,
                                               POSTFLIGHT_TEXT,
                                               StringVar(master, ZERO_LAT, "postGnssLat"),
                                               StringVar(master, ZERO_LON, "postGnssLon"),
                                               StringVar(master, ZERO_ALT, "postGnssAlt"))


        self.preflight_location.pack()
        # self.tilt_spin = TiltAndSpin(self.map_column, "offVert", "gyroZ")
        # self.tilt_spin.grid(row=4, column=0, padx=PADX, pady=PADY, sticky=(N,E,S,W))

        # self.status = TelemetryStatus(self.map_column, "radioPacketNum", "time", "gnssSatellites")
        # self.status.grid(row=4, column=1, padx=PADX, pady=PADY, sticky=(N,E,S,W))
        # self.map_column.rowconfigure(4, weight=0)

        self.status_bar = Frame(self, bg=Colors.BG_COLOR)
        self.status_bar.pack(side=BOTTOM, expand=False, fill=X, padx=PADX, pady=PADY)

        self.status_label = Label(self.status_bar, font=Fonts.MEDIUM_FONT, text="Disconnected", bg=Colors.BG_COLOR, fg=Colors.LIGHT_GRAY, anchor=E, justify="left")
        self.status_label.pack(side=BOTTOM, expand=False, fill=X)


    def set_state(self, state: DecoderState):
        match state:
            case DecoderState.OFFLINE:  # Default sate
                self.__reset__pack__()

            case DecoderState.PREFLIGHT:
                self.name_label.pack(after=self.telemetry_state_label, side=LEFT, expand=True, fill=X)
                self.callsign_label.pack(after=self.name_label, side=LEFT, expand=False, fill=NONE, padx=PADX)
                self.cont_label.pack(before=self.event_name_label, side=LEFT, expand=True, fill=X, padx=PADX)
                self.cont_event_frame.pack(after=self.name_callsign_state_frame, side=TOP, expand=False, fill=X, padx=PADX, pady=PADY)
                self.preflight_location.pack(after=self.map_frame, side=TOP, expand=False, fill=X, padx=PADX, pady=PADY)

            case DecoderState.INFLIGHT:
                self.cont_label.pack_forget()
                self.current_location.pack(after=self.preflight_location, side=TOP, expand=False, fill=X, padx=PADX, pady=PADY)

            case DecoderState.POSTFLIGHT:
                self.postflight_location.pack(after=self.current_location, side=TOP, expand=False, fill=X, padx=PADX, pady=PADY)

            case DecoderState.MAXES:
                pass

            case DecoderState.LAUNCH:
                self.setvar("launch_time", "0.0")
                self.map_frame.set_launch_point(float(self.getvar("launch_latitude")),
                                                float(self.getvar("launch_longitude")))
            case DecoderState.LAND:
                self.setvar("landing_time", "0.0")
                self.map_frame.set_landing_point(float(self.getvar("landing_latitude")),
                                                 float(self.getvar("landing_longitude")))

            case DecoderState.ERROR:
                pass

    def __reset__pack__(self):
        self.name_label.pack_forget()
        self.callsign_label.pack_forget()
        self.cont_event_frame.pack_forget()
        self.preflight_location.pack_forget()
        self.current_location.pack_forget()
        self.postflight_location.pack_forget()

    def reset(self):
        self.__reset__pack__()
        self.bytes_read.set(0)
        self.map_frame.reset()

class MapFrame(PanedWindow):
    def __init__(self,
                 master,
                 lat_var,
                 lon_var,
                 alt_var,
                 offline_maps_only_var):
        Frame.__init__(self, master, bg="cyan")

        self.lat_var = lat_var
        self.lon_var = lon_var
        self.alt_var = alt_var

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
        self.map_view.pack(expand=True, fill=BOTH)

        self.sats_label = Label(self.map_view, font=Fonts.MEDIUM_FONT_BOLD, text="# Sats", bg=Colors.GRAY, fg=Colors.WHITE, anchor=E, justify="left")
        self.sats_label.place(relx=1, x=-20, y=20, anchor=NE)

        self.fix_label = Label(self.map_view, font=Fonts.MEDIUM_FONT_BOLD, text="Good Fix", bg=Colors.GRAY, fg=Colors.DARK_GREEN, anchor=E, justify="left")
        self.fix_label.place(relx=1, x=-20, y=50, anchor=NE)

        self.reset()


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
        self.map_view.pack(expand=True, fill=BOTH)


class LocationRow(Frame):
    def __init__(self,
                 master,
                 name,
                 lat_var,
                 lon_var,
                 alt_var,
                 fg:  str = "#FFFFFF",
                 bg: str = "#0F0F0F"):

        Frame.__init__(self, master, bg=bg)

        self.name = Label(self, text=name, width=6, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="right")
        self.name.grid(row=0, column=0, sticky=(N,S), padx=PADX, pady=PADY)

        self.lat = Label(self, textvariable=lat_var, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="center")
        self.lat.grid(row=0, column=1, sticky=(N,E,W,S), padx=PADX, pady=PADY)

        self.lon = Label(self, textvariable=lon_var, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="center")
        self.lon.grid(row=0, column=2, sticky=(N,E,W,S), padx=PADX, pady=PADY)

        self.alt = Label(self, width=5, textvariable=alt_var, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="center")
        self.alt.grid(row=0, column=3, sticky=(N,S), padx=PADX, pady=PADY)

        self.columnconfigure((0,3), weight=0)
        self.columnconfigure((1,2), weight=1, uniform="b")
