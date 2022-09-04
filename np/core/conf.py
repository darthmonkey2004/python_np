from np.core.xrandr import xrandr
from np.core.log import np_logger
import os
import pickle
import pathlib

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
	log(f"WARNING: deprecated initConf running from conf.py!!!", 'warning')
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
	conf['pbdl_url'] = None
	conf['DATA_DIR'] = (f"{home}{os.path.sep}.np")
	conf['LOGFILE'] = f"{conf['DATA_DIR']}/nplayer.log"
	conf['CONFFILE'] = f"{conf['DATA_DIR']}/nplayer.conf"
	conf['WSLOGFILE'] = (f"{conf['DATA_DIR']}{os.path.sep}nplayer.wslog")
	conf['CAPTURE_DIR'] = (f"{home}{os.path.sep}Pictures{os.path.sep}nplayer_caps")
	conf['SFTP_DIR'] = (f"{home}{os.path.sep}.np{os.path.sep}sftp")
	conf['DEFAULT_POSTER'] = (f"{home}{os.path.sep}.local{os.path.sep}poster.png")
	conf['COMFILE'] = (f"{conf['DATA_DIR']}{os.path.sep}nplayer.com")
	conf['EXEC_DIR'] = (f"{home}/.local/lib/python3.8/site-packages/np")
	#ret = writeConf(conf)
	return conf

def run_setup():
	keys = ['play_type', 'play_types', 'screen', 'fullscreen', 'screens', 'scale', 'volume', 'rotate', 'shuffle', 'mute', 'video_methods', 'video_players', 'screens', 'nowplaying', 'vlc', 'network_modes', 'network_mode', 'remote', 'debug', 'init', 'GUI_RESET', 'window', 'pbdl_url', 'DATA_DIR', 'LOGFILE', 'CONFFILE', 'WSLOGFILE', 'CAPTURE_DIR', 'SFTP_DIR', 'media_directories', 'DEFAULT_POSTER	', 'COMFILE']
	conf = {}
	for key in keys:
		conf[key] = {}
	log("Starting interactive configuration setup...", 'info')
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
	conf['play_type'] = 'series'
	conf['play_types'] = ['series', 'movies', 'videos', 'music']
	screen = 0
	conf['screen'] = screen
	conf['screens'] = np.xrandr()
	conf['scale'] = 0.0
	conf['volume'] = 100
	conf['vlc']['opts'] = '--no-xlib'
	conf['rotate'] = 0
	conf['shuffle'] = True
	conf['mute'] = False
	conf['video_method'] = 'internal'
	conf['video_methods'] = ['external', 'internal']
	conf['video_player'] = 'vlc'
	conf['video_players'] = ['vlc', 'mplayer', 'mpv', 'cv2']
	conf['nowplaying']['filepath'] = None
	conf['nowplaying']['play_pos'] = None
	conf['windows'] = np.init_window_position()
	conf['GUI_RESET'] = False
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
	conf['remote']['server'] = {}
	conf['remote']['states'] = [0, 1]
	conf['remote']['server']['pid'] = None
	pick = None
	pick = input("Enable remote control server? (y/n)")
	if pick == 'n' or pick is None:
		conf['remote']['server']['state'] = 0
		conf['remote']['server']['port'] = 8000
		conf['remote']['server']['address'] = '127.0.0.1'
	elif pick == 'y':
		conf['remote']['server']['state'] = 1
		add = input("enter address of player machine: ")
		port = input("select a port to use: ")
		conf['remote']['server']['port'] = int(port)
		conf['remote']['server']['address'] = add
	conf['debug'] = False
	conf['init'] = True
	conf['GUI_RESET'] = False
	home = os.path.expanduser("~")
	conf['pbdl_url'] = None
	conf['DATA_DIR'] = (f"{home}{os.path.sep}.np")
	conf['LOGFILE'] = f"{conf['DATA_DIR']}{os.path.sep}nplayer.log"
	conf['CONFFILE'] = f"{conf['DATA_DIR']}{os.path.sep}nplayer.conf"
	conf['WSLOGFILE'] = (f"{conf['DATA_DIR']}{os.path.sep}nplayer.wslog")
	conf['CAPTURE_DIR'] = (f"{home}{os.path.sep}Pictures{os.path.sep}nplayer_caps")
	conf['SFTP_DIR'] = (f"{home}{os.path.sep}.np{os.path.sep}sftp")
	conf['DEFAULT_POSTER'] = (f"{home}{os.path.sep}.local{os.path.sep}poster.png")
	conf['COMFILE'] = (f"{conf['DATA_DIR']}{os.path.sep}nplayer.com")
	conf['ssh'] = {}
	conf['ssh']['connection_string'] = input("Please enter ssh connection string i.e. user@host: (blank for None):")
	
	
	
	ret = writeConf(conf)
	return conf
if __name__ == "__main__":
	run_setup()
