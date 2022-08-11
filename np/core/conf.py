from np.core.xrandr import xrandr
from np.core.log import np_logger
import os
import pickle

log = np_logger().log_msg
user = os.path.expanduser("~")
DATA_DIR = (user + os.path.sep + ".np")
CONFFILE = (DATA_DIR + os.path.sep + 'nplayer.conf')

def readConf():
	try:
		with open(CONFFILE, 'rb') as f:
			data = pickle.load(f)
		f.close()
		return data
	except Exception as e:
		print ("Exception in conf.py, readConf, line 70:", e)
		return None


def writeConf(data):
	try:
		with open(CONFFILE, 'wb') as f:
			pickle.dump(data, f)
		f.close()
		
		log('core.py, writeConf: Conf updated!', 'info')
		return True
	except Exception as e:
		print(f"Exception in conf.py, writeConf, line 83:{e}")
		return False


def initConf():
	global user
	#print ("Init conf running!")
	conf = {}
	conf['play_type'] = 'series'
	conf['play_types'] = ['series', 'movies', 'videos', 'music']
	conf['screen'] = 1
	conf['fullscreen'] = 1
	conf['screens'] = {}
	conf['scale'] = 0
	conf['volume'] = 100
	conf['rotate'] = 0
	conf['shuffle'] = False
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
	conf['init'] = True
	conf['GUI_RESET'] = False
	conf['window'] = {}
	conf['media_directories'] = {}
	log("Starting interactive directory setup...", 'info')
	media_dirs = None
	media_dirs = input("Enter media storage directory (see readme file in git download folder for details) ")
	if media_dirs is None:
		txt = ("Error: no media directory entered! Aborting...")
		return
	else:
		conf['media_directories'] = {}
		conf['media_directories']['main'] = media_dirs
		music_dir = (media_dirs + os.path.sep + "Music")
		movies_dir = (media_dirs + os.path.sep + "Movies")
		series_dir = (media_dirs + os.path.sep + "Series")
		conf['media_directories']['movies'] = movies_dir
		conf['media_directories']['music'] = music_dir
		conf['media_directories']['series'] = series_dir
		log("Media directories configured! Continuing...", 'info')
	home = os.path.expanduser("~")
	conf['DATA_DIR'] = (f"{home}{os.path.sep}.np")
	conf['LOGFILE'] = f"{conf['DATA_DIR']}/nplayer.log"
	conf['CONFFILE'] = f"{conf['DATA_DIR']}/nplayer.conf"
	conf['WSLOGFILE'] = (f"{conf['DATA_DIR']}{os.path.sep}nplayer.wslog")
	conf['CAPTURE_DIR'] = (f"{home}{os.path.sep}Pictures{os.path.sep}nplayer_caps")
	conf['SFTP_DIR'] = (f"{home}{os.path.sep}.np{os.path.sep}sftp")
	conf['DEFAULT_POSTER'] = (f"{home}{os.path.sep}.local{os.path.sep}poster.png")
	conf['COMFILE'] = (f"{conf['DATA_DIR']}{os.path.sep}nplayer.com")
	ret = writeConf(conf)
	return conf







