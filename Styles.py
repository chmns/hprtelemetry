from enum import Enum, StrEnum

class Fonts(StrEnum):
    SMALL_FONT = "Arial 10"
    MEDIUM_FONT = "Arial 16"
    MEDIUM_FONT_BOLD = "Arial 16 bold"
    LARGE_FONT = "Arial 32"
    LARGE_FONT_BOLD = "Arial 32 bold"
    MONO_FONT = "Courier 16 bold"

class Colors(StrEnum):
    BG_COLOR = "#0f0f0f"
    FG_COLOR = "#eeeeee"
    BLACK = "#000000"
    WHITE = "#ffffff"
    GRAY = "#333333"
    LIGHT_GRAY = "#aaaaaa"

    ALTITUDE_COLOR = "#8BD3E6"
    VELOCITY_COLOR = "#FF6D6A"
    ACCELERATION_COLOR = "#EFBE7D"
    DARK_RED = "#AA3333"
    DARK_GREEN = "#33AA33"