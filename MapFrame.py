from tkinter import *
from tkintermapview import TkinterMapView, OfflineLoader
from tkintermapview.utility_functions import osm_to_decimal
from Styles import Fonts, Colors
from TelemetryDecoder import DecoderState
import os # for maps db
from enum import StrEnum

DEFAULT_LAT = 44.7916443
DEFAULT_LON = -0.5995578
OFFLINE_ZOOM_MIN = 5
OFFLINE_ZOOM_MAX = 19
MIN_PATH_POINTS = 2
DEFAULT_ZOOM = 10
AUTOFOLLOW_ZOOM = 19

START_TEXT =      "  Start:"
LAUNCH_TEXT =     " Launch:"
LANDING_TEXT =    "Landing:"

PRELIGHT_TEXT =   "    Pre:"
CURRENT_TEXT =    " Flight:"
POSTFLIGHT_TEXT = "   Post:"

ZERO_LAT = "0.000000"
ZERO_LON = "0.000000"
ZERO_ALT = "0"

PADX = 4
PADY = 4

DEFAULT_DATABASE_NAME = "offline_tiles.db"
TILE_SERVER_URL = "http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}&s=Ga"

class NumberLabel(Frame):
    def __init__(self, master, name: str, textvariable: Variable, units: str,
                 font: str = Fonts.MEDIUM_FONT_BOLD, fg: str = Colors.WHITE, bg: str = Colors.BLACK) -> None:

        super().__init__(master, bg=bg)

        self.name_label = Label(self, text=name, anchor=E, font=font, bg=Colors.BG_COLOR, fg=fg)
        self.name_label.pack(side=LEFT, expand=True, fill=X)

        self.value_label = Label(self, textvariable=textvariable, font=font, bg=Colors.BG_COLOR, fg=fg)
        self.value_label.pack(side=LEFT, expand=False, fill=None)

        self.units_label = Label(self, text=units, anchor=W, font=font, bg=Colors.BG_COLOR, fg=fg)
        self.units_label.pack(side=LEFT, expand=True, fill=X)


class MapColumn(PanedWindow):
    def __init__(self, master):
        PanedWindow.__init__(self, orient="vertical", background=Colors.BLACK)

        self.total_bytes_read = StringVar(master, name="total_bytes_read")
        self.event_name = StringVar(master, "", "eventName")
        self.name = StringVar(master, "", "name")
        self.callsign = StringVar(master, "", "callsign")
        self.telemetry_state_name = StringVar(master, "", "telemetryStateName")
        self.cont_name = StringVar(master, "", "contName")
        self.currently_receiving = BooleanVar(master, name="currently_receiving")
        self.currently_receiving.trace_add("write", self.update_status_indicator)
        self.time_since_last_packet = DoubleVar(master, name="time_since_last_packet")

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

        self.preflight_location = LocationRow(self,
                                              PRELIGHT_TEXT,
                                              StringVar(master, ZERO_LAT, "preGnssLatString"),
                                              StringVar(master, ZERO_LON, "preGnssLonString"),
                                              StringVar(master, ZERO_ALT, "preGnssAltString"))
        # self.preflight_location.on_click = lam

        self.current_location = LocationRow(self,
                                            CURRENT_TEXT,
                                            StringVar(master, ZERO_LAT, "gnssLatString"),
                                            StringVar(master, ZERO_LON, "gnssLonString"),
                                            StringVar(master, ZERO_ALT, "gnssAltString"))

        self.postflight_location = LocationRow(self,
                                               POSTFLIGHT_TEXT,
                                               StringVar(master, ZERO_LAT, "postGnssLatString"),
                                               StringVar(master, ZERO_LON, "postGnssLonString"),
                                               StringVar(master, ZERO_ALT, "postGnssAltString"))

        self.launch_location = LocationRow(self,
                                           LAUNCH_TEXT,
                                           StringVar(master, ZERO_LAT, "launch_latitude"),
                                           StringVar(master, ZERO_LON, "launch_longitude"),
                                           StringVar(master, ZERO_ALT, "launch_time"))

        self.landing_location = LocationRow(self,
                                            LANDING_TEXT,
                                            StringVar(master, ZERO_LAT, "landing_latitude"),
                                            StringVar(master, ZERO_LON, "landing_longitude"),
                                            StringVar(master, ZERO_ALT, "landing_time"))

        self.map_frame = MapFrame(self, master)
        self.map_frame.pack(side=TOP, expand=True, fill=BOTH)

        self.status_bar = Frame(self, bg=Colors.BG_COLOR)
        self.status_bar.pack(side=BOTTOM, expand=False, fill=X)

        self.last_packet_indicator = Label(self.status_bar, textvariable=self.time_since_last_packet, font=Fonts.SMALL_MONO_FONT, bg=Colors.BRIGHT_RED, fg=Colors.WHITE)
        self.last_packet_indicator.pack(side=RIGHT, fill=X, ipadx=PADX*2, padx=PADX*2, pady=PADY*2)

        self.status_label = Label(self.status_bar, font=Fonts.MEDIUM_FONT, text="Disconnected", bg=Colors.BG_COLOR, fg=Colors.LIGHT_GRAY, anchor=E, justify="left")
        self.status_label.pack(side=RIGHT, fill=Y, padx=PADX, pady=PADY)

        self.tilt_roll_frame = Frame(self, bg=Colors.BG_COLOR)

        self.tilt = NumberLabel(self.tilt_roll_frame, name="Tilt:", textvariable=StringVar(master, "0", "offVert"), units="°")
        self.tilt.pack(side=LEFT, expand=True, fill=X, padx=PADX)

        self.roll = NumberLabel(self.tilt_roll_frame, name="Turns:", textvariable=StringVar(master, "0", "turns"), units="")
        self.roll.pack(side=LEFT, expand=True, fill=X, padx=PADX)

        self.turns = NumberLabel(self.tilt_roll_frame, name="Roll:", textvariable=StringVar(master, "0", "boundRoll"), units="°")
        self.turns.pack(side=LEFT, expand=True, fill=X, padx=PADX)


        # Statistics bar
        # ==============
        # Data:
        self.stats_frame = Frame(self, bg=Colors.BG_COLOR)
        self.stats_frame.pack(side=BOTTOM, after=self.status_bar, expand=False, fill=X, padx=PADX)

        self.total_bytes_read_label = NumberLabel(self.stats_frame, name="Data:", textvariable=StringVar(master, name="total_bytes_read"), units="")
        self.total_bytes_read_label.grid(column = 1, row = 0, sticky=(N,W,E,S))

        self.bytes_per_second_label = NumberLabel(self.stats_frame, name="", textvariable=StringVar(master, name="bytes_per_sec"), units="/s")
        self.bytes_per_second_label.grid(column = 2, row = 0, sticky=(N,W,E,S))

        self.total_bad_bytes_label = NumberLabel(self.stats_frame, name="Error:", textvariable=StringVar(master, name="total_bad_bytes_read"), units="")
        self.total_bad_bytes_label.grid(column = 3, row = 0, sticky=(N,W,E,S))

        # Messages:
        self.flt_time_label = NumberLabel(self.stats_frame, name="FltTime:", textvariable=StringVar(master, name="fltTime"), units="")
        self.flt_time_label.grid(column = 0, row = 1, sticky=(N,W,E,S))

        self.total_messages_read_label = NumberLabel(self.stats_frame, name="Packets:", textvariable=StringVar(master, name="total_messages_decoded"), units="Pkt")
        self.total_messages_read_label.grid(column = 1, row = 1, sticky=(N,W,E,S))

        self.messages_per_second_label = NumberLabel(self.stats_frame, name="", textvariable=StringVar(master, name="messages_per_sec"), units="Pkt/s")
        self.messages_per_second_label.grid(column = 2, row = 1, sticky=(N,W,E,S))

        self.total_bad_messages_label = NumberLabel(self.stats_frame, name="Error:", textvariable=StringVar(master, name="total_bad_messages"), units="Pkt")
        self.total_bad_messages_label.grid(column = 3, row = 1, sticky=(N,W,E,S))

        for r in range(2):
            self.stats_frame.rowconfigure(r, weight=1)

        for c in range(4):
            self.stats_frame.columnconfigure(c, weight=1, uniform="1")


    def load_offline_database(self, database_path):
        self.map_frame.load_offline_database(database_path)

    # def delete_map(self):
        # self.map_frame.delete_map()

    def set_status_text(self, text,
                        color:str = None,
                        bg: str = None):

        self.status_label.config(text=text)

        if color is not None:
            self.status_label.config(fg=color)

        if bg is None:
            bg = Colors.BG_COLOR

        self.status_label.config(bg=bg)
        self.status_bar.config(bg=bg)

    def set_state(self, state: DecoderState):

        if self.map_frame.state == DecoderState.OFFLINE and state != DecoderState.OFFLINE:
            self.name_label.pack(after=self.telemetry_state_label, side=LEFT, expand=True, fill=X)
            self.callsign_label.pack(after=self.name_label, side=LEFT, expand=False, fill=NONE, padx=PADX)
            self.cont_label.pack(before=self.event_name_label, side=LEFT, expand=True, fill=X, padx=PADX)
            self.cont_event_frame.pack(after=self.name_callsign_state_frame, side=TOP, expand=False, fill=X, padx=PADX)
            self.preflight_location.pack(after=self.map_frame, side=TOP, expand=False, fill=X, padx=PADX)
            self.tilt_roll_frame.pack(side=BOTTOM, after=self.stats_frame, expand=False, fill=X, padx=PADX, pady=PADY)

        if state == DecoderState.INFLIGHT:
            self.current_location.pack(after=self.preflight_location, side=TOP, expand=False, fill=X, padx=PADX)

        if state == DecoderState.POSTFLIGHT:
            self.current_location.pack(after=self.preflight_location, side=TOP, expand=False, fill=X, padx=PADX)
            self.postflight_location.pack(after=self.current_location, side=TOP, expand=False, fill=X, padx=PADX)

        if state == DecoderState.OFFLINE:
            self.__reset__pack__()

        if state == DecoderState.LAUNCH:
            self.setvar("launch_time", "0.0")
            self.map_frame.update_marker(state,
                                         float(self.getvar("launch_latitude")),
                                         float(self.getvar("launch_longitude")))
            self.launch_location.pack(after=self.preflight_location, side=TOP, expand=False, fill=X, padx=PADX)

        if state == DecoderState.LAND:
            self.setvar("landing_time", "0.0")
            self.map_frame.update_marker(state,
                                         float(self.getvar("landing_latitude")),
                                         float(self.getvar("landing_longitude")))
            try:
                self.landing_location.pack(after=self.postflight_location, side=TOP, expand=False, fill=X, padx=PADX)
            except Exception:
                self.landing_location.pack(after=self.current_location, side=TOP, expand=False, fill=X, padx=PADX)

        self.map_frame.state = state


    def update_status_indicator(self, *_):
        if self.currently_receiving.get():
            self.last_packet_indicator.config(bg=Colors.BRIGHT_GREEN, fg=Colors.GRAY)
        else:
            self.last_packet_indicator.config(bg=Colors.BRIGHT_RED, fg=Colors.WHITE)



    def update_data(self):
        self.map_frame.update_data()

    def __reset__pack__(self):
        self.name_label.pack_forget()
        self.callsign_label.pack_forget()
        self.cont_event_frame.pack_forget()
        self.preflight_location.pack_forget()
        self.current_location.pack_forget()
        self.postflight_location.pack_forget()
        self.launch_location.pack_forget()
        self.landing_location.pack_forget()
        self.tilt_roll_frame.pack_forget()


    def reset(self):
        self.__reset__pack__()
        self.total_bytes_read.set(0)
        self.map_frame.reset()

class MapFrame(PanedWindow):
    def __init__(self, master, window):
        Frame.__init__(self, master,bg=Colors.BG_COLOR)

        self.prevLat = 0.0
        self.prevLon = 0.0

        self.markers = { state : None for state in DecoderState }

        self.lat = DoubleVar(window, name="gnssLat")
        self.lon = DoubleVar(window, name="gnssLon")
        self.alt = DoubleVar(window, name="gnssAlt")

        self.preLat = DoubleVar(window, name="preGnssLat")
        self.preLon = DoubleVar(window, name="preGnssLon")

        self.postLat = DoubleVar(window, name="postGnssLat")
        self.postLon = DoubleVar(window, name="postGnssLon")

        self.sats_var = IntVar(window, 0, "gnssSatellites")
        self.sats_var.trace_add("write", self.update_num_sats)

        self.fix_var = BooleanVar(window, False, "gnssFix")
        self.fix_var.trace_add("write", self.update_fix)

        self.offline_maps_only = BooleanVar(window, name="offline_maps_only")
        self.offline_maps_only.trace_add("write", self.set_offline_maps_only)

        self.autofollow = BooleanVar(self, True, name="autofollow")
        self.autofollow.trace_add("write", self.center_map)

        script_directory = os.path.dirname(os.path.abspath(__file__))
        self.database_path = os.path.join(script_directory, DEFAULT_DATABASE_NAME)

        # print(f"Online maps downloading enabled?: {self.offline_maps_only.get()}")
        # print(f"Using offline maps database at: {self.database_path}")

        self.map_view = TkinterMapView(self,
                                       database_path=self.database_path,
                                       use_database_only=self.offline_maps_only.get())
        self.map_view.set_tile_server(TILE_SERVER_URL)
        self.map_view.pack(expand=True, fill=BOTH)

        self.sats_label = Label(self, font=Fonts.MEDIUM_FONT_BOLD, text="", bg=Colors.GRAY, anchor=E)
        self.sats_label.place(relx=1, x=-20, y=20, anchor=NE)
        self.update_num_sats()

        self.fix_label = Label(self, font=Fonts.MEDIUM_FONT_BOLD, text="", bg=Colors.GRAY, anchor=E, padx=PADX, pady=PADY)
        self.fix_label.place(relx=1, x=-20, y=50, anchor=NE)
        self.update_fix()

        self.zoom_label = Label(self, font=Fonts.MEDIUM_FONT_BOLD, text=self.map_view.zoom, bg=Colors.GRAY, fg=Colors.LIGHT_GRAY, anchor=E, padx=PADX, pady=PADY)
        self.zoom_label.place(relx=1, rely=1, x=-20, y=-20, anchor=SE)

        self.online_label = Label(self, font=Fonts.MEDIUM_FONT_BOLD, text=self.map_view.zoom, bg=Colors.GRAY, fg=Colors.DARK_RED, anchor=E, padx=PADX, pady=PADY)
        self.online_label.place(relx=1, rely=0, x=20, y=-20, anchor=SW)

        self.autofollow_checkbox = Checkbutton(self, variable=self.autofollow, text="Auto-follow", font=Fonts.MEDIUM_FONT, bg=Colors.GRAY, fg=Colors.LIGHT_GRAY, anchor=W, padx=PADX, pady=PADY)
        self.autofollow_checkbox.place(relx=0, rely=1, x=20, y=-20, anchor=SW)

        self.state = DecoderState.OFFLINE

        self.map_view.canvas.bind("<ButtonRelease-1>", self.mouse_release)
        self.map_view.canvas.bind("<MouseWheel>", self.mouse_zoom)

        self.reset()
        self.__update_zoom_label__()

    def center_map(self, *_):
        if not self.autofollow.get():
            return

        match self.state:
            case DecoderState.PREFLIGHT:
                self.map_view.set_position(self.preLat.get(), self.preLon.get())
            case DecoderState.INFLIGHT:
                self.map_view.set_position(self.lat.get(), self.lon.get())
            case DecoderState.POSTFLIGHT:
                self.map_view.set_position(self.postLat.get(), self.postLon.get())

    def set_offline_maps_only(self, *_):
        offline_only = self.offline_maps_only.get()
        self.map_view.use_database_only = offline_only

        # hack to get maps to start loading when online is re-enabled
        if not offline_only:
            current_zoom = self.map_view.zoom
            self.map_view.set_zoom(current_zoom+1)
            self.map_view.set_zoom(current_zoom)

    def mouse_release(self, event):
        self.map_view.mouse_release(event)
        self.__update_zoom_label__()

    def mouse_zoom(self, event):
        self.map_view.mouse_zoom(event)
        self.__update_zoom_label__()

    def __update_zoom_label__(self):
        self.zoom_label.config(text=f"Zoom: {self.map_view.zoom:.1f}")

    def update_num_sats(self, *_):
        num_sats = self.sats_var.get()
        self.sats_label.config(text=f"{num_sats} Satellites")

        if num_sats > 0:
            self.sats_label.config(fg=Colors.WHITE)
        else:
            self.sats_label.config(fg=Colors.LIGHT_GRAY)

    def update_fix(self, *_):
        if self.fix_var.get():
            self.fix_label.config(text=f"Good Fix", fg=Colors.DARK_GREEN)
        else:
            self.fix_label.config(text=f"No Fix", fg=Colors.DARK_RED)

    def set_online(self, online: bool):
        if online:
            self.online_label.config(text=f"Online", fg=Colors.DARK_GREEN)
        else:
            self.online_label.config(text=f"Offline", fg=Colors.DARK_RED)

    def update_data(self):
        changed = False

        new_lat = self.prevLat
        new_lon = self.prevLon

        match self.state:
            case DecoderState.OFFLINE:
                return
            case DecoderState.PREFLIGHT:
                new_lat = self.preLat.get()
                new_lon = self.preLon.get()
            case DecoderState.INFLIGHT:
                new_lat = self.lat.get()
                new_lon = self.lon.get()
            case DecoderState.POSTFLIGHT:
                new_lat = self.postLat.get()
                new_lon = self.postLon.get()

        if self.prevLat != new_lat:
            self.prevLat = new_lat
            changed = True

        if self.prevLon != new_lon:
            self.prevLon = new_lon
            changed = True

        if not changed:
            return

        try:
            self.map_view.set_position(new_lat, new_lon)
        except Exception:
            return

        if self.autofollow.get():
            try:
                self.map_view.set_position(new_lat, new_lon)
                self.map_view.set_zoom(AUTOFOLLOW_ZOOM)
                self.__update_zoom_label__()

            except Exception:
                return

        if self.state == DecoderState.PREFLIGHT:
            self.update_marker(self.state, new_lat, new_lon)
            return

        if self.state == DecoderState.POSTFLIGHT:
            self.update_marker(self.state, new_lat, new_lon)
            return

        # hacky way to do it but can't get the method in documentation
        # working. need to have at least 2 points before creating path
        # and then after that you append to it, rather than setting it
        if self.path is None:
            if len(self.path_list) > MIN_PATH_POINTS:
                self.path = self.map_view.set_path(self.path_list, width=2)
            else:
                self.path_list.append((new_lat, new_lon))
        else:
            self.path.add_position(new_lat, new_lon)

    def update_marker(self, state: DecoderState, lat: float, lon:float) -> None:
        marker = self.markers[state]
        if marker is None:
            self.markers[state] = self.map_view.set_marker(lat, lon, state.name)
        else:
            marker.set_position(lat, lon)

    def reset(self) -> None:
        self.map_view.set_position(DEFAULT_LAT, DEFAULT_LON)
        self.map_view.set_zoom(DEFAULT_ZOOM)
        self.map_view.delete_all_path()
        self.path_list = []
        self.path = None
        self.map_view.delete_all_marker()
        for entry in self.markers:
            self.markers[entry] = None
        self.update_num_sats()
        self.update_fix()

    def download_current_map(self):
        current_zoom = round(self.map_view.zoom)
        current_position = self.map_view.get_position()
        top_left_position = osm_to_decimal(*self.map_view.upper_left_tile_pos, current_zoom)
        bottom_right_position = osm_to_decimal(*self.map_view.lower_right_tile_pos, current_zoom)

        print(f"Attempting to download region bound by: {top_left_position} and {bottom_right_position}")
        print(f"From zoom level: {current_zoom} to {OFFLINE_ZOOM_MAX}")

        self.map_view.set_position(*current_position)

        downloader = OfflineLoader(path=self.database_path, tile_server=TILE_SERVER_URL)

        downloader.save_offline_tiles(top_left_position,
                                        bottom_right_position,
                                        current_zoom,
                                        OFFLINE_ZOOM_MAX)

        self.map_view.set_position(*current_position)


    def load_offline_database(self, database_path):
        print(f"Setting offline map file to: {database_path}")
        self.database_path = database_path
        self.map_view.pack_forget()
        del self.map_view

        self.map_view = TkinterMapView(self,
                                       database_path=self.database_path,
                                       use_database_only=self.offline_maps_only.get())
        self.map_view.set_tile_server(TILE_SERVER_URL)
        self.map_view.pack(expand=True, fill=BOTH)
        self.sats_label.lift()
        self.fix_label.lift()
        self.zoom_label.lift()
        self.online_label.lift()
        self.autofollow_checkbox.lift()
        self.reset()

    # def delete_map(self):
        # del self.map_view

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

        self.name = Label(self, text=name, width=8, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="right")
        self.name.grid(row=0, column=0, sticky=(N,W,E,S), padx=PADX, pady=PADY)

        self.lat = Label(self, textvariable=lat_var, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="center")
        self.lat.grid(row=0, column=1, sticky=(N,E,W,S), padx=PADX, pady=PADY)

        self.lon = Label(self, textvariable=lon_var, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="center")
        self.lon.grid(row=0, column=2, sticky=(N,E,W,S), padx=PADX, pady=PADY)

        self.alt = Label(self, width=5, textvariable=alt_var, bg=bg, fg=fg, font=Fonts.MONO_FONT, justify="center")
        self.alt.grid(row=0, column=3, sticky=(N,W,E,S), padx=PADX, pady=PADY)

        self.columnconfigure((0,3), weight=0)
        self.columnconfigure((1,2), weight=1)

        self.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        pass
