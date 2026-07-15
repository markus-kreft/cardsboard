import configparser
import locale
import os
import sys
from os.path import expanduser, exists


# Default config parameters
DATADIR = expanduser("~/.config/cardsboard/data")
COLUMN_WIDTH = 35
ITEM_HEIGHT = 3
COLOR_NORMAL_FG = "white"
COLOR_NORMAL_BG = "black"
COLOR_FOCUSED_FG = "red"
COLOR_FOCUSED_BG = "black"
COLOR_WARN_FG = "white"
COLOR_WARN_BG = "red"
COLOR_TAGGED_FG = "yellow"
COLOR_TAGGED_BG = "black"


CONF_FILE = expanduser("~/.config/cardsboard/config.ini")
CONF = configparser.ConfigParser()


# If non config file exists, make one with the default parameters
if not exists(CONF_FILE):
    try:
        os.makedirs(os.path.dirname(CONF_FILE), exist_ok=True)
    except OSError:
        pass
    with open(CONF_FILE, "w", encoding=locale.getpreferredencoding()) as conf_file:
        CONF.add_section("main")
        CONF.set("main", "datadir", str(DATADIR))
        CONF.set("main", "column_width", str(COLUMN_WIDTH))
        CONF.set("main", "item_height", str(ITEM_HEIGHT))
        CONF.add_section("colors")
        CONF.set("colors", "normal_fg", COLOR_NORMAL_FG)
        CONF.set("colors", "normal_bg", COLOR_NORMAL_BG)
        CONF.set("colors", "focused_fg", COLOR_FOCUSED_FG)
        CONF.set("colors", "focused_bg", COLOR_FOCUSED_BG)
        CONF.set("colors", "warn_fg", COLOR_WARN_FG)
        CONF.set("colors", "warn_bg", COLOR_WARN_BG)
        CONF.set("colors", "tagged_fg", COLOR_TAGGED_FG)
        CONF.set("colors", "tagged_bg", COLOR_TAGGED_BG)
        CONF.write(conf_file)
try:
    CONF.read(CONF_FILE)
except configparser.ParsingError as err:
    print(f"Config file error: {err}")
    sys.exit()


# Load config to global variables, using defaults as fallback
DATADIR = CONF.get("main", "datadir", fallback=DATADIR)
COLUMN_WIDTH = int(CONF.get("main", "column_width", fallback=COLUMN_WIDTH))
ITEM_HEIGHT = int(CONF.get("main", "item_height", fallback=ITEM_HEIGHT))
CMD = CONF.get("main", "cmd", fallback=None)
CMD_TMUX = CONF.get("main", "cmd_tmux", fallback=None)
COLOR_FOCUSED_FG = CONF.get("colors", "focused_fg", fallback=COLOR_FOCUSED_FG)
COLOR_FOCUSED_BG = CONF.get("colors", "focused_bg", fallback=COLOR_FOCUSED_BG)
COLOR_NORMAL_FG = CONF.get("colors", "normal_fg", fallback=COLOR_NORMAL_FG)
COLOR_NORMAL_BG = CONF.get("colors", "normal_bg", fallback=COLOR_NORMAL_BG)
COLOR_WARN_FG = CONF.get("colors", "warn_fg", fallback=COLOR_WARN_FG)
COLOR_WARN_BG = CONF.get("colors", "warn_bg", fallback=COLOR_WARN_BG)
COLOR_TAGGED_FG = CONF.get("colors", "tagged_fg", fallback=COLOR_TAGGED_FG)
COLOR_TAGGED_BG = CONF.get("colors", "tagged_bg", fallback=COLOR_TAGGED_BG)


ITEM_WIDTH = COLUMN_WIDTH - 2

if not exists(DATADIR):
    os.mkdir(DATADIR)
