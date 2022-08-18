import vlc
import os
import pathlib
from np.core.log import np_logger
from np.core.core import init_window_position
from np.core.xrandr import xrandr
log = np_logger().log_msg
from np.utils.guess_intro import guess_intro
from np.utils.xrandr import xrandr
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
from np.utils import cleandb
from np.core.conf import initConf, readConf, writeConf
from np.utils.music_mgr import music_mgr
#from np.utils import torrent_mgr as pbdl_mgr
from np.utils.query_series import tmdb_query_series as query_series
from np.core.core import *
from np.core.gui import gui
from np.core.nplayer import nplayer
#from np.utils.gui_create import add_elem
#add_elem = add_elem()
#create = add_elem.create
#create_element = add_elem.create_element
from np.utils.pbdl_se_isin import se_isin
from np.utils.pbdl import pbdl
from np.utils.query_series import tmdb_query_series as lookup_series
from np.utils.query_series import get_sinfo_from_filepath as seinfo
from np.utils.query_movies import query_imdb as lookup_movies
from np.core.nplayer_db import addtodb
from np.utils.tadb_search import lookup as lookup_music
from np.utils.scan_music import scan_music
from np.utils.scan_series import scan_series
from np.utils.scan_movies import scan_movies
from np.utils.scan_all import scan_all
from np.utils.scan_all import scan_all as mediascan
#from np.utils.ytdl import ytdl
from np.core.conf import run_setup
from np.utils.pbdl_add_to_series import add_series
from np.utils.set_media_paths import set_media_paths
from np.utils.id3 import tag
from np.ws import websocket_server
from np.ws import server
from np.ws import client
from np.ws import thread
home = os.path.expanduser("~")
try:
	conf = readConf()
	log("Conf read!", 'info')
	DATA_DIR = conf['DATA_DIR']
	LOGFILE = conf['LOGFILE']
	WSLOGFILE = conf['WSLOGFILE']
	CAPTURE_DIR = conf['CAPTURE_DIR']
	CONFFILE = conf['CONFFILE']
	SFTP_DIR = conf['SFTP_DIR']
	MEDIA_DIR = conf['media_directories']['main']
	MUSIC_DIR = conf['media_directories']['music']
	MOVIES_DIR = conf['media_directories']['movies']
	SERIES_DIR = conf['media_directories']['series']
	COMFILE = conf['COMFILE']
	DEFAULT_POSTER = conf['DEFAULT_POSTER']
	log("__init__.py:Read directory data from conf!", 'info')
except Exception as e:
	log(f"__init__.py:Unable to read conf: {e}", 'error')
	conf = initConf()
	DATA_DIR = conf['DATA_DIR']
	LOGFILE = conf['LOGFILE']
	WSLOGFILE = conf['WSLOGFILE']
	CAPTURE_DIR = conf['CAPTURE_DIR']
	CONFFILE = conf['CONFFILE']
	SFTP_DIR = (conf['SFTP_DIR'])
	MEDIA_DIR = conf['media_directories']['main']
	MUSIC_DIR = conf['media_directories']['music']
	MOVIES_DIR = conf['media_directories']['movies']
	SERIES_DIR = conf['media_directories']['series']
	COMFILE = conf['COMFILE']
	log(f"__init__.py:Unable to read directory data from conf: {e}. Defaults used.", 'error')


if not os.path.exists(conf['CONFFILE']):
	log(f"conf file doesn't exist, creating...", 'warning')
	com = (f"touch '{CONFFILE}'")
	subprocess.check_output(com, shell=True)
if not os.path.exists(COMFILE):
	log(f"command file doesn't exist, creating...", 'warning')
	com = (f"touch '{COMFILE}'")
	subprocess.check_output(com, shell=True)

try:
	init = conf['init']
	if init == True:
		pass
	else:
		log(f"conf init is False, re-initializing...", 'info')
		conf = initConf()
		conf['windows'] = init_window_position()
		log(f"__init__.py; init ran on conf and window positions", 'info')
		writeConf(conf)
except Exception as e:
	log(f"__init__.py; Exception in init file: {e}", 'error')
	conf = initConf()
	try:
		test = conf['windows']
	except Exception as e:
		conf['windows'] = init_window_position()
		log(f"Ran init_window_position() while handling exception in __init__.py; {e}", 'warning')
	writeConf(conf)


pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
pathlib.Path(SFTP_DIR).mkdir(parents=True, exist_ok=True)

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
err = err().err


