import pathlib
import os
import subprocess
from np.utils.xrandr import xrandr
from np.utils.scan_all import *

"""TODO: Remove create_log() from init, replace with this script on logfile exception.
TODO: change DEFAULT_POSTER location throughout np to DATA_DIR (not local)
TODO: add NPLAYER_LOGO variable, set in .local to use as icon."""

DATA_DIR = os.path.join(os.path.expanduser("~"), ".np")
LOGFILE = os.path.join(DATA_DIR, 'nplayer.log')
CONFFILE = os.path.join(DATA_DIR, 'nplayer.conf')
SFTP_DIR = os.path.join(DATA_DIR, 'sftp')
WSLOGFILE = os.path.join(DATA_DIR, 'nplayer.wslog')
CAPTURE_DIR = os.path.join(os.path.expanduser("~"), 'Pictures', 'nplayer_caps')
NPLAYER_LOGO = os.path.join(os.path.expanduser("~"), ".local", "poster.png")
DEFAULT_POSTER = os.path.join(DATA_DIR, 'poster.png')

def test_data_dir():
	if not os.path.exists(DATA_DIR):
		pathlib.Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
	return True

def test_sftp_dir():
	if not os.path.exists(SFTP_DIR):
		pathlib.Path(SFTP_DIR).mkdir(parents=True, exist_ok=True)
	return True

def test_cap_dir():
	if not os.path.exists(CAPTURE_DIR):
		pathlib.Path(CAPTURE_DIR).mkdir(parents=True, exist_ok=True)
	return True

def test_log_file():
	if not os.path.exists(LOGFILE):
		ret = subprocess.check_output(f"touch \"{LOGFILE}\"", shell=True).decode().strip()
		if ret == '':
			ret = True
			msg = None
		else:
			msg = ret
			ret = False
	else:
		ret = True
		msg = None
	return ret, msg

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


def initConf(media_path=None):
	if media_path is None:
		print("No media path provided. Using default!")
		media_path = '/var/storage'
	user = os.getlogin()
	conf = {}
	conf['play_type'] = 'series'
	conf['play_types'] = ['series', 'movies', 'videos', 'music']
	screen = None
	screens = []
	for screen in xrandr().keys():
		if xrandr()[screen]['connected']:
			screens.append(screen)
	screen = screens[0]
	conf['screen'] = screen
	conf['fullscreen'] = 1
	conf['screens'] = screens
	conf['scale'] = 0
	conf['volume'] = 100
	conf['rotate'] = 0
	conf['shuffle'] = False
	conf['mute'] = False
	conf['video_method'] = 'internal'
	conf['video_methods'] = ['external', 'internal']
	conf['video_player'] = 'vlc'
	conf['video_players'] = ['vlc', 'mplayer', 'mpv', 'cv2']
	conf['nowplaying'] = {}
	conf['nowplaying']['filepath'] = '/var/storage/Series/Archer/S9/Archer.S9E3.Different Modes of Preparing the Fruit.mp4'
	conf['nowplaying']['play_pos'] = 0
	conf['vlc'] = {}
	conf['vlc']['opts'] = '--no-xlib'
	conf['network_modes'] = {}
	conf['network_modes']['control_modes'] = ['local', 'remote', 'server']
	conf['network_modes']['media_modes'] = ['local', 'remote']
	conf['network_mode'] = {}
	conf['network_mode']['media_mode'] = 'local'
	conf['network_mode']['media_host'] = None
	conf['network_mode']['media_user'] = os.getlogin()
	conf['network_mode']['control_mode'] = 'local'
	conf['network_mode']['control_host'] = None
	conf['network_mode']['control_user'] = os.getlogin()
	conf['network_mode']['control_port'] = 4444
	conf['remote'] = {}
	conf['remote']['server'] = {}
	conf['remote']['server']['pid'] = None
	conf['remote']['server']['state'] = 1
	conf['remote']['server']['port'] = 8000
	conf['remote']['server']['address'] = get_local_ip()
	conf['remote']['states'] = [0, 1]
	conf['debug'] = True
	conf['init'] = True
	conf['GUI_RESET'] = False
	conf['media_directories'] = {}
	conf['media_directories']['main'] = media_path
	conf['media_directories']['movies'] = os.path.join(media_path, 'Movies')
	conf['media_directories']['music'] = os.path.join(media_path, 'Music')
	conf['media_directories']['series'] = os.path.join(media_path, 'Series')
	conf['pbdl_url'] = None
	conf['DATA_DIR'] = os.path.join(os.path.expanduser("~"), '.np')
	conf['LOGFILE'] = os.path.join(conf['DATA_DIR'], 'nplayer.log')
	conf['CONFFILE'] = os.path.join(conf['DATA_DIR'], 'nplayer.conf')
	conf['WSLOGFILE'] = os.path.join(conf['DATA_DIR'], 'nplayer.wslog')
	conf['CAPTURE_DIR'] = os.path.join(os.path.expanduser("~"), 'Pictures', 'nplayer_caps')
	conf['SFTP_DIR'] = os.path.join(conf['DATA_DIR'], 'sftp')
	conf['DEFAULT_POSTER'] = os.path.join(os.path.expanduser("~"), '.local', 'poster.png')
	conf['exit_ok'] = False
	conf['windows'] = {}
	for screen in screens:
		xdata = xrandr()
		conf['windows'][screen] = {}
		#viewer_screen = get_opposite_screen(screen)
		conf['windows'][screen]['browser'] = {}
		conf['windows'][screen]['browser']['x'] = xdata[screen]['pos_x']
		conf['windows'][screen]['browser']['y'] = xdata[screen]['pos_y']
		conf['windows'][screen]['browser']['w'] = 600
		conf['windows'][screen]['browser']['h'] = 150
		conf['windows'][screen]['gui'] = {}
		conf['windows'][screen]['gui']['x'] = xdata[screen]['pos_x']
		conf['windows'][screen]['gui']['y'] = xdata[screen]['pos_y']
		conf['windows'][screen]['gui']['w'] = 1024
		conf['windows'][screen]['gui']['h'] = 600
		conf['windows'][screen]['viewer'] = {}
		conf['windows'][screen]['viewer']['x'] = xdata[screen]['pos_x']
		conf['windows'][screen]['viewer']['y'] = xdata[screen]['pos_y']
		conf['windows'][screen]['viewer']['w'] = xdata[screen]['w']
		conf['windows'][screen]['viewer']['h'] = xdata[screen]['h']
	conf['intro'] = {}
	conf['intro']['start'] = None
	conf['intro']['end'] = None
	conf['load_inactive'] = False
	conf['max_playlist_items'] = 200
	conf['play_mode'] = 'database'
	return conf


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


def run_setup():
	test_data_dir()
	test_sftp_dir()
	test_log_file()
	test_cap_dir()
	if not os.path.exists(CONFFILE):
		print(f"conf file doesn't exist, creating...")
		conf = initConf()
		writeConf(conf)
	keys = ['play_type', 'play_types', 'screen', 'fullscreen', 'screens', 'scale', 'volume', 'rotate', 'shuffle', 'mute', 'video_methods', 'video_players', 'screens', 'nowplaying', 'vlc', 'network_modes', 'network_mode', 'remote', 'debug', 'init', 'GUI_RESET', 'window', 'pbdl_url', 'LOGFILE', 'CONFFILE', 'WSLOGFILE', 'CAPTURE_DIR', 'SFTP_DIR', 'media_directories', 'DEFAULT_POSTER']
	conf = {}
	conf['load_inactive'] = False
	conf['max_playlist_items'] = 200
	for key in keys:
		conf[key] = {}
	print("Starting interactive configuration setup...")
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
		print("Media directories configured! Continuing...")
	conf['play_type'] = 'series'
	conf['play_mode'] = 'database'
	conf['play_types'] = ['series', 'movies', 'videos', 'music']
	screen = 0
	conf['screen'] = screen
	conf['screens'] = xrandr()
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
	conf['network_mode']['media_user'] = os.getlogin()
	conf['network_mode']['control_mode'] = 'local'
	conf['network_mode']['control_host'] = None
	conf['network_mode']['control_user'] = os.getlogin()
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
	conf['DATA_DIR'] = DATA_DIR
	conf['LOGFILE'] = LOGFILE
	conf['CONFFILE'] = CONFFILE
	conf['WSLOGFILE'] = WSLOGFILE
	conf['CAPTURE_DIR'] = CAPTURE_DIR
	conf['SFTP_DIR'] = SFTP_DIR
	conf['DEFAULT_POSTER'] = DEFAULT_POSTER
	conf['ssh'] = {}
	conf['ssh']['connection_string'] = input("Please enter ssh connection string i.e. user@host: (blank for None):")
	conf['exit_ok'] = False
	ret = writeConf(conf)
	print("Scanning for media files. This could take a while... maybe grab a cup of coffee????")
	scan_all()
