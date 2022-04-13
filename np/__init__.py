import os
from np.utils.xrandr import xrandr
from np.utils import nplayer_db as sqldb
from np.utils.nplayer_db import querydb
from np.utils.nplayer_db import updatedb
from np.utils.nplayer_db import removefromdb
from np.utils.nplayer_db import get_columns
from np.utils.nplayer_db import addtodb_new
from np.utils.music_mgr import music_mgr
from np.utils.tmdb_query_series import lookup as series_lookup
from np.utils.tmdb_query_series import tmdb_query_series as query_series
from np.utils.input_handler import input_handler as dev
from np.utils import torrent_mgr as pbdl_mgr
from np.utils import input_handler as dev
from np.utils import tmdb_query_series as tmdb_series
from np.core.core import *
from np.core.gui import gui
from np.core.nplayer import nplayer
from np.utils.gui_create import add_elem
add_elem = add_elem()
create = add_elem.create
create_element = add_elem.create_element
from np.utils.pbdl_se_isin import se_isin
from np.utils.pbdl import pbdl
from np.utils.tmdb_query_series import tmdb_query_series as lookup_series
from np.utils.tmdb_query_series import get_sinfo_from_filepath as seinfo
from np.utils.nplayer_db import addtodb
from np.utils.pbdl_dl import get_url, get_results_api
from np.utils.scan_music import scan_music
from np.main import start
MUSIC_DIR = 'var/storage/Music'
