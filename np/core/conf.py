from np.utils.xrandr import xrandr
from np.core.log import np_logger
import os
import pickle

log = np_logger().log_msg
main_keys = ['viewer', 'gui', 'pbdl', 'w', 'h', 'x', 'y', 'pbdl_dl', 'ytdl', 'browser', 'is_default']
ui_windows = ['browser', 'ytdl', 'pbdl', 'pbdl_dl', 'gui', 'viewer']



def readConf():
	conf_file = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.conf')
	try:
		with open(conf_file, 'rb') as f:
			data = pickle.load(f)
		f.close()
		return data
	except Exception as e:
		log(f"Exception in conf.py, readConf: {e}", 'error')
		return None


def writeConf(data):
	conf_file = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.conf')
	try:
		with open(conf_file, 'wb') as f:
			pickle.dump(data, f)
		f.close()
		
		log('core.py, writeConf: Conf updated!', 'info')
		return True
	except Exception as e:
		log(f"Exception in conf.py, writeConf: {e}", 'info')
		return False

def initConf():
	global user
	log(f"WARNING: deprecated initConf running from conf.py!!!", 'warning')
	conf = {}
	conf['max_playlist_items'] = 200
	conf['play_mode'] = 'database'
	conf['load_inactive'] = False
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
	conf['network_mode']['media_user'] = os.path.expanduser("~").split('/home/')[1]
	conf['network_mode']['control_mode'] = 'local'
	conf['network_mode']['control_host'] = None
	conf['network_mode']['control_user'] = os.path.expanduser("~").split('/home/')[1]
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
		music_dir = os.path.join(media_dirs, "Music")
		movies_dir = os.path.join(media_dirs, "Movies")
		series_dir = os.path.join(media_dirs, "Series")
		conf['media_directories']['movies'] = movies_dir
		conf['media_directories']['music'] = music_dir
		conf['media_directories']['series'] = series_dir
		log("Media directories configured! Continuing...", 'info')
	home = os.path.expanduser("~")
	conf['pbdl_url'] = None
	conf['DATA_DIR'] = os.path.join(os.path.expanduser("~"), '.np')
	conf['LOGFILE'] = os.path.join(conf['DATA_DIR'], 'nplayer.log')
	conf['CONFFILE'] = os.path.join(conf['DATA_DIR'], 'nplayer.conf')
	conf['WSLOGFILE'] = os.path.join(conf['DATA_DIR'], 'nplayer.wslog')
	conf['CAPTURE_DIR'] = os.path.join(os.path.expanduser("~"), 'Pictures', 'nplayer_caps')
	conf['SFTP_DIR'] = os.path.join(conf['DATA_DIR'], 'sftp')
	conf['DEFAULT_POSTER'] = os.path.join(os.path.expanduser("~"), ".local", "poster.png")
	#conf['EXEC_DIR'] = (f"{home}/.local/lib/python3.8/site-packages/np")
	conf['exit_ok'] = False
	#ret = writeConf(conf)
	return conf

def run_setup():
	data_dir = os.path.join(os.path.expand_user("~"), '.np')
	sftp_dir = os.path.join(data_dir, 'sftp')
	pathlib.Path(data_dir).mkdir(parents=True, exist_ok=True)
	pathlib.Path(sftp_dir).mkdir(parents=True, exist_ok=True)
	conf_file = os.path.join(data_dir, 'nplayer.conf')
	if not os.path.exists(conf_file):
		log(f"conf file doesn't exist, creating...", 'warning')
		conf = initConf()
		writeConf(conf)
	keys = ['play_type', 'play_types', 'screen', 'fullscreen', 'screens', 'scale', 'volume', 'rotate', 'shuffle', 'mute', 'video_methods', 'video_players', 'screens', 'nowplaying', 'vlc', 'network_modes', 'network_mode', 'remote', 'debug', 'init', 'GUI_RESET', 'window', 'pbdl_url', 'LOGFILE', 'CONFFILE', 'WSLOGFILE', 'CAPTURE_DIR', 'SFTP_DIR', 'media_directories', 'DEFAULT_POSTER']
	conf = {}
	conf['load_inactive'] = False
	conf['max_playlist_items'] = 200
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
		music_dir = os.path.join(media_dirs, "Music")
		movies_dir = os.path.join(media_dirs, "Movies")
		series_dir = os.path.join(media_dirs, "Series")
		conf['media_directories']['movies'] = movies_dir
		conf['media_directories']['music'] = music_dir
		conf['media_directories']['series'] = series_dir
		log("Media directories configured! Continuing...", 'info')
	conf['play_type'] = 'series'
	conf['play_mode'] = 'database'
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
	# initialize window defaults by passing conf and getting it back
	conf = init_window_position(conf)
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
	conf['DATA_DIR'] = os.path.join(os.path.expanduser("~"), '.np')
	conf['LOGFILE'] = os.path.join(conf['DATA_DIR'], 'nplayer.log')
	conf['CONFFILE'] = os.path.join(conf['DATA_DIR'], 'nplayer.conf')
	conf['WSLOGFILE'] = os.path.join(conf['DATA_DIR'], 'nplayer.wslog')
	conf['CAPTURE_DIR'] = os.path.join(os.path.expanduser("~"), 'Pictures', 'nplayer_caps')
	conf['SFTP_DIR'] = os.path.join(conf['DATA_DIR'], 'sftp')
	conf['DEFAULT_POSTER'] = os.path.join(os.path.expanduser("~"), ".local", "poster.png")
	conf['ssh'] = {}
	conf['ssh']['connection_string'] = input("Please enter ssh connection string i.e. user@host: (blank for None):")
	conf['exit_ok'] = False
	ret = writeConf(conf)
	return conf


def test_primary_screen(test_screen):
	for screen in [screen for screen in list(xrandr().keys())]:
		if xrandr()[screen]['primary'] is True:
			if test_screen == screen:
				return True
			else:
				return False


def init_window_position(conf=None):
	if conf is None:
		conf = readConf()
	conf['xrandr'] = xrandr()
	conf['screens'] = list(conf['xrandr'].keys())
	conf['windows'] = {}
	for screen in conf['screens']:
		if not xrandr()[screen]['connected']:
			pass
		else:
			conf['windows'][screen] = {}
			conf['windows'][screen]['is_default'] = test_primary_screen(screen)
			for win_title in ui_windows:
				conf['windows'][screen][win_title] = {}
				if win_title == 'viewer':
					conf['windows'][screen][win_title]['x'] = conf['xrandr'][screen]['pos_x']
					conf['windows'][screen][win_title]['y'] = conf['xrandr'][screen]['pos_y']
					conf['windows'][screen][win_title]['w'] = conf['xrandr'][screen]['w']
					conf['windows'][screen][win_title]['h'] = conf['xrandr'][screen]['h']
				elif win_title == 'gui':
					conf['windows'][screen][win_title]['x'] = conf['xrandr'][screen]['pos_x']
					conf['windows'][screen][win_title]['y'] = conf['xrandr'][screen]['pos_y']
					conf['windows'][screen][win_title]['w'] = 1024
					conf['windows'][screen][win_title]['h'] = 600
				elif win_title == 'pbdl':
					conf['windows'][screen][win_title]['x'] = conf['xrandr'][screen]['pos_x']
					conf['windows'][screen][win_title]['y'] = conf['xrandr'][screen]['pos_y']
					conf['windows'][screen][win_title]['w'] = 600
					conf['windows'][screen][win_title]['h'] = 300
				elif win_title == 'pbdl_dl':
					conf['windows'][screen][win_title]['x'] = conf['xrandr'][screen]['pos_x']
					conf['windows'][screen][win_title]['y'] = conf['xrandr'][screen]['pos_y']
					conf['windows'][screen][win_title]['w'] = 600
					conf['windows'][screen][win_title]['h'] = 300
				elif win_title == 'ytdl':
					conf['windows'][screen][win_title]['x'] = conf['xrandr'][screen]['pos_x']
					conf['windows'][screen][win_title]['y'] = conf['xrandr'][screen]['pos_y']
					conf['windows'][screen][win_title]['w'] = 750
					conf['windows'][screen][win_title]['h'] = 300
				elif win_title == 'browser':
					conf['windows'][screen][win_title]['x'] = conf['xrandr'][screen]['pos_x']
					conf['windows'][screen][win_title]['y'] = conf['xrandr'][screen]['pos_y']
					conf['windows'][screen][win_title]['w'] = 600
					conf['windows'][screen][win_title]['h'] = 150
	return conf


if __name__ == "__main__":
	run_setup()
