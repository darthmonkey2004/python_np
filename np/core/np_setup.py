import pickle
import pathlib
import os
import subprocess
from np.utils.xrandr import xrandr
from np.utils.scan_all import *
from np.utils.pbdl.utils import get_user_input, get_user_yn


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
main_keys = ['viewer', 'gui', 'pbdl', 'w', 'h', 'x', 'y', 'pbdl_dl', 'ytdl', 'browser', 'is_default']
ui_windows = ['browser', 'ytdl', 'pbdl', 'pbdl_dl', 'gui', 'viewer']



def test_primary_screen(test_screen):
	for screen in [screen for screen in list(xrandr().keys())]:
		if xrandr()[screen]['primary'] is True:
			if test_screen == screen:
				return True
			else:
				return False

def get_local_ip():
	com = "ip -o -4 a s | awk -F'[ /]+' '$2!~/lo/{print $4}' | grep \"192.168\""
	return subprocess.check_output(com, shell=True).decode().strip()

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
		
		log('np_setup.writeConf():Conf updated!', 'info')
		return True
	except Exception as e:
		log(f"Exception in np_setup.writeConf():: {e}", 'error')
		return False


def initConf(media_path=None):
	if media_path is None:
		log("np_setup.initConf():No media path provided. Using default!")
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
	conf['network'] = {}
	conf['network']['control_modes'] = ['local', 'remote', 'server']
	conf['network']['media'] = {}
	conf['network']['media']['available_modes'] = ['local', 'remote']
	conf['network']['media']['mode'] = 'local'
	conf['network']['media']['host'] = None
	conf['network']['media']['user'] = os.getlogin()
	conf['network']['control'] = {}
	conf['network']['control']['mode'] = 'local'
	conf['network']['control']['host'] = get_local_ip()
	conf['network']['control']['user'] = os.getlogin()
	conf['network']['control']['port'] = 8000
	conf['remote'] = {}
	conf['remote']['server'] = {}
	conf['remote']['server']['pid'] = None
	conf['remote']['server']['state'] = 1
	conf['remote']['server']['port'] = conf['network']['control']['port']
	conf['remote']['server']['address'] = conf['network']['control']['host']
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


def shell(com):
	try:
		out = subprocess.check_output(com, shell=True).decode().strip()
	except Exception as e:
		print("Error running command:", e)
		return None
	if out == '':
		out = None
	elif "\n" in out:
		out = out.splitlines()
	else:
		out = [out]
	return out

def get_mounts():
	try:
		com = f"ls -F --group-directories-first \"{SFTP_DIR}\" | grep \"/\" | cut -d \"/\" -f 1"
		dirs = shell(com)
		return dirs
	except Exception as e:
		print(f"No directories at {SFTP_DIR} ({e})!")
		return []


def create_mount(remote_path=None, connection_string=None):
	conf = readConf()
	if remote_path is None:
		remote_path = conf['network']['media']['path']
	if connection_string is None:
		user = conf['network']['media']['user']
		ip = conf['network_mode']['media']['host']
		if ip is None:
			ip = get_local_ip()
		connection_string = f"{user}@{ip}"
	name = os.path.basename(remote_path)
	mnt_path = conf['media_directories']['main']
	com = f"mkdir -p \"{mnt_path}\""
	ret = shell(com)
	if ret is not None:
		print("Couldn't create mount!", ret)
		return False
	com = f"sudo sshfs -o allow_other \"{connection_string}:{remote_path}\" \"{mnt_path}\""
	ret = shell(com)
	if ret is not None:
		print("couldn't create mount:", ret)
		return False
	else:
		return True

def test_mounts():
	if len(get_mounts()) == 0:
		print("Mount point doesn't exist! Creating...")
		ret = create_mount()
		if not ret:
			print("mount test failed!")
		return ret
	else:
		return True


def run_setup(media_dirs=None, enable_remote=None):
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
	if media_dirs is None:
		txt = "Enter media storage path. For samba/sftp, prefix remote path with 'smb://' or 'sftp://'."
		media_dirs = get_user_input(window_title='Set media directory:', txt=txt)
	if 'sftp://' in media_dirs:
		prefix = 'sftp://'
		media_dirs = media_dirs.split(prefix)[1]
		enable_remote = True
		print("sftp set!")
	elif 'smb://' in media_dirs:
		prefix = 'smb://'
		media_dirs = media_dirs.split(prefix)[1]
		enable_remote = True
		print("samba set!")
	else:
		prefix = None
		enable_remote = False
		print("local set!")
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
	conf['network'] = {}
	conf['network']['control_modes'] = ['local', 'remote', 'server']
	conf['network']['media'] = {}
	conf['network']['media']['available_modes'] = ['local', 'remote']
	if enable_remote:
		print("enabling remote storage...")
		conf['network']['media']['mode'] = 'remote'
		conf['network']['media']['host'] = get_user_input(window_title='Remote media storage ip address:', txt='Enter ip address for remote media storage machine:')
		default_user = get_user_yn(window_title=f"Use username {os.getlogin()}?")
		if not default_user:
			conf['network']['media']['user'] = get_user_input(window_title='Set username:', txt='Enter username for remote media storgage:')
			print("TODO: Add external script to use ssh-copy-id to remote host address using above username ({conf['network']['media']['user']})")
		else:
			conf['network']['media']['user'] = os.getlogin()
			print(f"Using default logged in username: {conf['network']['media']['user']}!")
		conf['network']['media']['path'] = media_dirs
		name = os.path.basename(media_dirs)
		main = os.path.join(SFTP_DIR, name)
		music = os.path.join(main, 'Music')
		series = os.path.join(main, 'Series')
		movies = os.path.join(main, 'Movies')
		conf['media_directories']['main'] = main
		conf['media_directories']['music'] = music
		conf['media_directories']['series'] = series
		conf['media_directories']['movies'] = movies
	else:
		print("using local media storage...")
		conf['network']['media']['mode'] = 'local'
		conf['network']['media']['host'] = get_local_ip()
		conf['network']['media']['path'] = None
	conf['network']['control'] = {}
	conf['network']['control']['mode'] = 'local'
	conf['network']['control']['host'] = get_local_ip()
	conf['network']['control']['user'] = os.getlogin()
	conf['network']['control']['port'] = 8000
	conf['remote'] = {}
	conf['remote']['server'] = {}
	conf['remote']['server']['pid'] = None
	if enable_remote is None:
		enable_remote = get_user_yn(window_title='Enable remote control server? (remotely control nplayer, this is different that remote media storage):')
	if not enable_remote:
		conf['remote']['server']['state'] = 0
		conf['remote']['server']['port'] = conf['network']['control']['port']
		conf['remote']['server']['address'] = get_local_ip()
	else:
		conf['remote']['server']['state'] = 1
		add = get_user_input(window_title='Setting up remote...', txt="Enter address of player machine:")
		port =  get_user_input(window_title='Setting up remote...', txt="Enter a port:")
		conf['remote']['server']['port'] = int(port)
		conf['remote']['server']['address'] = add
		conf['network']['control']['host'] = add
		conf['network']['control']['port'] = int(port)
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
	localip = get_local_ip()
	user = os.getlogin()
	ssh_conn_string = f"{user}@{localip}"
	conf['ssh']['connection_string'] = ssh_conn_string
	conf['exit_ok'] = False
	conf['tmdb_api_key'] = get_user_input(window_title='TMDB.org API key:', txt="This requires an api key from TMDB. You can get one here... (https://www.themoviedb.org/settings/api)")
	ret = writeConf(conf)
	print("Scanning for media files. This could take a while... maybe grab a cup of coffee????")
	if conf['network']['media']['mode'] == 'remote':
		ret = test_mounts()
		if not ret:
			print("Unable to mount storage! Fix it, try agian...")
			exit()
	scan_all()

if __name__ == "__main__":
	run_setup()
