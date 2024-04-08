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