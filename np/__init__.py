import vlc
import os
import pathlib
from np.utils.xrandr import xrandr
from np.core.log import np_logger
log = np_logger().log_msg
from np.utils.guess_intro import guess_intro
from np.utils.insert_intro import insert_intro
from np.core import nplayer_db as sqldb
from np.core.nplayer_db import querydb
from np.core.nplayer_db import updatedb
from np.core.nplayer_db import removefromdb
from np.core.nplayer_db import get_columns
from np.core.nplayer_db import addtodb_new
from np.core.nplayer_db import create_db
from np.core.nplayer_db import create_table_series
from np.core.nplayer_db import create_table_movies
from np.core.nplayer_db import create_table_music
from np.core.nplayer_db import test_db
from np.utils.cleandb import run as cleandb
from np.core.db_editor import db_editor
from np.utils.tag_editor import run as tag_editor
from np.core.conf import initConf, readConf, writeConf, run_setup
#from np.utils.pbdl import query_series
#from np.utils.pbdl import query_movies
from np.core.core import create_media, get_local_ip, get_res, enable_debug, disable_debug, read_history, write_history, set_play_type, calculate_scale, shell, check_process, python
from np.core.gui import folder_browse_window
from np.core.gui import gui
from np.core.gui import db_editor, bring_to_front, send_to_back, run_long_operation, write_event, restore, maximize, minimize, hide, un_hide, reappear, dissapear, get_pointer, start_thread
from np.core.nplayer import nplayer
DEFAULT_POSTER = None
#from np.utils.pbdl.se_isin import se_isin
#from np.utils.pbdl.ty_isin import ty_isin, parse_title
from np.core.nplayer_db import addtodb
from np.utils.tadb_search import lookup as lookup_music
from np.utils.scan_music import scan_music
from np.utils.scan_series import scan_series
from np.utils.scan_movies import scan_movies
from np.utils.scan_all import scan_all
from np.core.conf import run_setup
from np.utils.id3 import tag
from np.ws import websocket_server
from np.ws import server
from np.ws import client
from np.ws import thread
from np.utils.insert_intro import fix3d
from np.core.conf import init_window_position





red = (255, 0, 0)
orange = (255, 127.5, 0)
yellow = (255, 255, 0)
green = (0, 255, 0)
blue = (0, 255, 255)
indigo = (0, 0, 255)
violet = (255, 0, 255)
colors = [red, orange, yellow, green, blue, indigo, violet]
