import vlc
import os
import pathlib
from np.core.log import np_logger
from np.core.core import init_window_position
log = np_logger.log_msg
dir(log)
from np.utils.guess_intro import guess_intro
from np.utils.xrandr import xrandr
from np.core import nplayer_db as sqldb
from np.core.nplayer_db import querydb
from np.core.nplayer_db import updatedb
from np.core.nplayer_db import removefromdb
from np.core.nplayer_db import get_columns
from np.core.nplayer_db import addtodb_new as add_to_db
from np.core.nplayer_db import addtodb_new
from np.core.nplayer_db import create_db
from np.core.nplayer_db import test_db
from np.core.core import initConf
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
from np.core.nplayer_db import addtodb
from np.utils.scan_music import scan_music
from np.utils.scan_series import scan_series
from np.utils.scan_movies import scan_movies
from np.utils.ytdl import ytdl
from np.utils.init_conf import run_setup
home = os.path.expanduser("~")
DATA_DIR = (user + os.path.sep + ".np")
CONFFILE = f"{DATA_DIR}/nplayer.conf"

if not os.path.exists(CONFFILE):
	com = (f"touch '{CONFFILE}'")
	subprocess.check_output(com, shell=True)
	conf = initConf()
	writeConf(conf)
	conf['windows'] = init_window_position()
	writeConf(conf)

def readConf():
	with open(CONFFILE, 'rb') as f:
		data = pickle.load(f)
	f.close()
	return data
conf = readConf()
try:
	init = conf['init']
	if init == True:
		pass
	else:
		conf = initConf()
		conf['windows'] = init_window_position()
		writeConf(conf)
except Exception as e:
	np.log(f"__init__.py; Exception in init file: {e}", 'info')
	conf = initConf()
	conf['windows'] = init_window_position()
	writeConf(conf)

def writeConf(data):
	with open(CONFFILE, 'wb') as f:
		pickle.dump(data, f)
	f.close()
	log('core.py, writeConf: Conf updated!', 'info')
	return True

from np.utils.pbdl_add_to_series import add_series
import np.core.wsreceiver as receiver
import np.core.wsserver as server
import np.core.wssender as sender

#conf['GUI_RESET'] = False
#writeConf(conf)
#from np.main import start
home = os.path.expanduser("~")
DATA_DIR = (user + os.path.sep + ".np")
LOGFILE = (DATA_DIR + os.path.sep + 'nplayer.log')
WSLOGFILE = (DATA_DIR + os.path.sep + 'nplayer.wslog')
#DATA_DIR = (home + os.path.sep + ".np")
CAPTURE_DIR = (home + os.path.sep + "Pictures" + os.path.sep + "nplayer_caps")
pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
SFTP_DIR = (f"{home}{os.path.sep}.np{os.path.sep}sftp")
pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
try:
	pathlib.Path(SFTP_DIR).mkdir(parents=True, exist_ok=True)
except:
	pass
DEFAULT_POSTER = (home + os.path.sep + '.local' + os.path.sep + 'poster.png')
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

#log = log().log
err = err().err
COMFILE = (DATA_DIR + os.path.sep + 'nplayer.com')
try:
	MEDIA_DIR = conf['media_directories']['main']
	MUSIC_DIR = conf['media_directories']['music']
	MOVIES_DIR = conf['media_directories']['movies']
	SERIES_DIR = conf['media_directories']['series']
except Exception as e:
	print (f"init.py exception: {e}")
	from np.core import core
	core.set_media_paths()
	conf = readConf()
	MEDIA_DIR = conf['media_directories']['main']
	MUSIC_DIR = conf['media_directories']['music']
	MOVIES_DIR = conf['media_directories']['movies']
	SERIES_DIR = conf['media_directories']['series']	
