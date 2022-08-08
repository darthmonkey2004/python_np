import pickle
import os
from np.core.log import np_logger
from np.utils.xrandr import xrandr

log = np_logger().log_msg
user = os.path.expanduser("~")
DATA_DIR = (user + os.path.sep + ".np")
CONFFILE = (DATA_DIR + os.path.sep + 'nplayer.conf')

def initConf():
	global user
	conf = {}
	conf['play_type'] = 'series'
	conf['play_types'] = ['series', 'movies', 'videos', 'music']
	conf['screen'] = 1
	conf['fullscreen'] = 1
	conf['screens'] = {}
	conf['pos_x'] = None
	conf['pos_y'] = None
	conf['w'] = None
	conf['h'] = None
	conf['scale'] = 2.799999952316284
	conf['volume'] = 100
	conf['rotate'] = 0
	conf['shuffle'] = 1
	conf['mute'] = False
	conf['video_method'] = 'internal'
	conf['video_methods'] = ['external', 'internal']#select between external video player window and internal xwindow widget
	conf['video_player'] = 'vlc'
	conf['video_players'] = ['vlc', 'mplayer', 'mpv', 'cv2']# list of usuable playback engines (internal are cv2 and vlc, external are all
	screens = xrandr()
	conf['screens'] = screens
	conf['nowplaying'] = {}
	conf['nowplaying']['filepath'] = None
	conf['nowplaying']['play_pos'] = None
	conf['vlc'] = {}
	conf['vlc']['opts'] = "--no-xlib"
	conf['debug'] = True
	conf['network_modes'] = {}
	conf['network_modes']['control_modes'] = ['local', 'remote', 'server']
	conf['network_modes']['media_modes'] = ['local', 'remote']
	conf['network_mode'] = {}
	conf['network_mode']['media_mode'] = 'local'
	conf['network_mode']['media_host'] = None
	conf['network_mode']['media_user'] = user
	conf['network_mode']['control_mode'] = 'local'
	conf['network_mode']['control_host'] = None
	conf['network_mode']['control_user'] = user
	conf['network_mode']['control_port'] = 4444
	conf['remote'] = {}
	conf['debug'] = False
	return conf


def readConf():
	try:
		with open(CONFFILE, 'rb') as f:
			data = pickle.load(f)
		f.close()
		return data
	except Exception as e:
		log(f"Exception in conf_mgr.py, readConf, line 66: {e}", 'error')
		return False


def writeConf(data, conf_file=None):
	if conf_file == None:
		global CONFFILE
		conf_file = CONFFILE
	try:
		with open(conf_file, 'wb') as f:
			pickle.dump(data, f)
		f.close()
		ret = log('conf_mgr.py, line 79, writeConf: Conf updated!', 'info')
		return True
	except Exception as e:
		log(f"Exception in conf_mgr.py, writeConf, line 82:{e}", 'error')
		return False
