import vlc
import os
import pathlib

from np.utils.guess_intro import guess_intro
from np.utils.xrandr import xrandr
from np.utils import nplayer_db as sqldb
from np.utils.nplayer_db import querydb
from np.utils.nplayer_db import updatedb
from np.utils.nplayer_db import removefromdb
from np.utils.nplayer_db import get_columns
from np.utils.nplayer_db import addtodb_new as add_to_db
from np.utils.nplayer_db import addtodb_new
from np.utils.music_mgr import music_mgr
from np.utils.input_handler import input_handler as dev
#from np.utils import torrent_mgr as pbdl_mgr
from np.utils import input_handler as dev
from np.utils.query_series import tmdb_query_series as query_series
from np.core.core import *
from np.core.gui import gui
from np.core.nplayer import nplayer
from np.utils.gui_create import add_elem
add_elem = add_elem()
create = add_elem.create
create_element = add_elem.create_element
from np.utils.pbdl_se_isin import se_isin
from np.utils.pbdl import pbdl
from np.utils.query_series import tmdb_query_series as lookup_series
from np.utils.query_series import get_sinfo_from_filepath as seinfo
from np.utils.query_movies import query_imdb as lookup_movies
from np.utils.nplayer_db import addtodb
from np.utils.scan_music import scan_music
from np.utils.ytdl import ytdl
from np.utils.init_conf import run_setup
from np.utils.pbdl_add_to_series import add_series
#from np.main import start
home = os.path.expanduser("~")
CAPTURE_DIR = (home + os.path.sep + "Pictures" + os.path.sep + "nplayer_caps")
DATA_DIR = (home + os.path.sep + ".np")
pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
afilters = []
vfilters = []
for f in vlc.Instance().video_filter_list_get():
	n, x, y, x = f
	name = n.decode()
	name = ("video:" + name)
	vfilters.append(name)
for f in vlc.Instance().audio_filter_list_get():
	n, x, y, x = f
	name = n.decode()
	name = ("audio:" + name)
	afilters.append(name)
VLC_VIDEO_FILTERS = sorted(vfilters)
VLC_AUDIO_FILTERS = sorted(afilters)
