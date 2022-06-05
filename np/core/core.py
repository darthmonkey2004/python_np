import datetime
import PySimpleGUI as sg
import requests
import logging
import vlc
import pickle
import os
import inspect
from np.utils.xrandr import xrandr
import pickle
from videoprops import get_video_properties
from np.core.nplayer_db import querydb
import np

user = os.getlogin()
npdir = (os.path.sep + "home" + os.path.sep + user + os.path.sep + ".np")
todo = (npdir + os.path.sep + "todo.txt")
if os.path.exists(todo):
	with open(todo, 'r') as f:
		lines = f.read()
	f.close()
	print (lines)
	#for line in lines:
		#print (line)
DISPLAY_INFO = xrandr()
KEY_EVENTS = {}
KEY_EVENTS['SEEK_FWD'] = 208
KEY_EVENTS['SEEK_REV'] = 168
KEY_EVENTS['SCALE_UP'] = 165
KEY_EVENTS['SCALE_DOWN'] = 163
KEY_EVENTS['FULLSCREEN'] = 164
KEY_EVENTS['PAUSE'] = 113
KEY_EVENTS['SKIP_NEXT'] = 115
KEY_EVENTS['SKIP_PREV'] = 114
sep = os.path.sep
conf_file=(npdir + sep + "nplayer.conf")


def get_local_ip():
	com = "ip -o -4 a s | awk -F'[ /]+' '$2!~/lo/{print $4}'"
	return subprocess.check_output(com, shell=True).decode().strip()


def initConf():
	global user
	#print ("Init conf running!")
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
	#conf['watched_devices'] = ['/dev/input/event11', '/dev/input/event2']
	#conf['grab_devices'] = ['/dev/input/event11']
	ret = writeConf(conf)
	return conf

class log():
	def __init__(self):
		global conf
		self.conf = conf
		self.log_type = 'debug'
		self.msg = None
		t = datetime.datetime.now()
		self.ts = (str(t.day) + "-" + str(t.month) + "-" + str(t.year) + " " + str(t.hour) + ":" + str(t.minute) + ":" + str(t.second) + ":" + str(t.microsecond))
		try:
			self.debug = self.conf['debug']
		except Exception as e:
			print (f"Error: debug setting not in conf: {e}")
	def log(self, *args):
		pos = -1
		for arg in args:
			pos = pos + 1
			if pos == 0:
				self.msg = (self.ts + "--" + str(arg))
			elif pos == 1:
				self.log_type = arg
		self.log_level = getattr(logging, self.log_type.upper(), None)
		if not isinstance(self.log_level, int):
			raise ValueError('Invalid log level: %s' % self.log_type)
			return
		logging.basicConfig(filename=np.LOGFILE, level=self.log_level)
		if self.msg == None:
			raise ValueError('No message data provided!')
		if self.debug == True:
			print ("DEBUG MESSAGE:", self.msg)
		if self.log_level == 10:#debug level
			logging.debug(self.msg)
		elif self.log_level == 20:
			logging.info(self.msg)
		elif self.log_level == 30:
			logging.warning(self.msg)
		elif self.log_level == 40:
			logging.error(self.msg)
			try:
				print("Nplayer logged an error:", self.msg)
			except Exception as e:
				ouch=("Unable to print error message, background process(?)", self.msg, e)
				logging.error(ouch)
				raise RuntimeError(ouch) from e
				return
		return


def readConf():
	try:
		with open(conf_file, 'rb') as f:
			data = pickle.load(f)
		f.close()
		return data
	except Exception as e:
		print ("Exception in core.py, readConf, line 87:", e)
		return None
conf = readConf()

def writeConf(data):
	try:
		logger = log().log
	except:
		pass
	try:
		with open(conf_file, 'wb') as f:
			pickle.dump(data, f)
		f.close()
		
		logger('core.py, writeConf: Conf updated!', 'info')
		return True
	except Exception as e:
		print(f"Exception in core.py, writeConf, line 149:{e}")
		return False


class err():
	def __init__(self):
		self.logger = log()
		self.log = self.logger.log
		self.err_type = None
		self.msg = None
	def err(self, *args):
		pos = -1
		for arg in args:
			pos = pos + 1
			if pos == 0:
				self.msg = arg
			elif pos == 1:
				self.err_type = arg
		if self.err_type is None:
			self.err_type = RuntimeError
		if self.msg == None:
			self.log("No error message data provided!", 'error')
			raise RuntimeError('No message data provided!')
			return
		else:
			self.log(self.msg, 'error')
			raise self.err_type(self.msg)
			return



if not os.path.exists(conf_file):
	conf = initConf()
history_file = (npdir + sep + "nplayer.series.history")
logfile = (npdir + sep + "nplayer.log")
gui_conf_file = (npdir + sep + "np.gui.conf")
pyfile = (npdir + os.path.sep + "temp_gui.py")
if not os.path.exists(npdir):
	os.makedirs(npdir)



def get_res(filepath):
	try:
		props = get_video_properties(filepath)
		w = props['width']
		h = props['height']
		out = (w, h)
		return out
	except Exception as e:
		print ("Get res failed!:", e)
		return None



def enable_debug():
	conf = readConf()
	conf['debug'] = True
	writeConf(conf)
	log("Debug enabled!", 'info')


def disable_debug():
	conf = readConf()
	conf['debug'] = False
	writeConf(conf)
	log("Debug disabled!", 'info') 


def updateConf(conf, key, val):
	log('core.py.updateConf running from somewhere...', 'debug')
	conf = readConf()
	key = str(key)
	keys = list(conf.keys())
	if key in keys:
		conf[key] = val
		writeConf(conf)
		log("Conf updated!", 'info')
		return True
	else:
		log(f"key not found: {key}", 'error')
		return False


def read_history():
	history_dict = {}
	try:
		with open (history_file, 'rb') as f:
			history_dict = pickle.load(f)
		f.close()			
	except Exception as e:
		print ("Exception in core.py, read_history, line 159:", e)
	return history_dict


def write_history(history_dict):
	try:
		with open (history_file, 'wb') as f:
			pickle.dump(history_dict, f)
		f.close()
		return True
	except Exception as e:
		print ("Exception in core.py, write_history, line 170:", e)
		return False


def set_play_type(play_type):
	play_type = play_type
	conf['play_type'] = play_type
	writeConf(conf)
	np.log('core.py, set_play_type: Conf file written!', 'info')


def calculate_scale(_file, conf=None, _type='file'):
	if _type != 'file':
		print ("type is not file, cannot calculate scale:", _type)
		return False
	if conf == None:
		conf = readConf()
	if not os.path.exists(_file):
		print ("File not found:,", _file)
		return False
	vw, vh = get_res(_file)
	screen = conf['screen']
	h = int(conf['screens'][screen]['h'])
	w = int(conf['screens'][screen]['w'])
	if vw is None or vh is None or h is None or w is None:
		return False
	if vw == 0 or vh == 0 or h == 0 or w == 0:
		return False
	if h >= vh and w >= vw:
		sw = h / vh
		sh = w / vw
	elif h <= vh and w <= vw:
		sw = vh / h
		sh = w / vw
	else:
		sw = 1.0
		sh = 1.0
	if sw <= sh:
		scale = float(sw)
	elif sw >= sh:
		scale = float(sh)
	else:
		scale = float(sw)
	return scale


if not os.path.exists(conf_file):
	conf = initConf()
else:
	conf = readConf()


def init_window_position():
	np.init_screens()


def create_media(play_type=None, rows=None):
	media = {}
	media['DBMGR_RESULTS'] = []
	if play_type == None:
		try:
			conf = readConf()
			play_type = conf['play_type']
		except:
			play_type = 'series'
	media['series_history'] = {}
	media['history_file'] = history_file
	media['is_playing'] = 0
	media['now_playing'] = {}
	media['current_vlc_media_object'] = None
	media['continuous'] = 1
	media['items'] = {}
	media['vlc'] = {}
	media['vlc']['events'] = ['2:EventType.MediaDurationChanged', '5:EventType.MediaStateChanged', '256:EventType.MediaMPMediaChanged', '260:EventType.MediaMPPlaying', '261:EventType.MediaMPPaused', '262:EventType.MediaMPStopped', '263:EventType.MediaMPForward', '264:EventType.MediaMPBackward', '265:EventType.MediaMPEndReached', '266:EventType.MediaMPEncounteredError', '267:EventType.MediaMPTimeChanged', '268:EventType.MediaMPPositionChanged', '269:EventType.MediaMPSeekableChanged', '270:EventType.MediaMPPausableChanged', '271:EventType.MediaMPTitleChanged', '272:EventType.MediaMPSnapshotTaken', '273:EventType.MediaMPLengthChanged', '274:EventType.MediaMPVout', '275:EventType.MediaMPScrambledChanged', '281:EventType.MediaMPMuted', '282:EventType.MediaMPUnmuted', '283:EventType.MediaMPAudioVolume', '284:EventType.MediaMPAudioDevice', '285:EventType.MediaMPChapterChanged', '1536:EventType.VlmMediaAdded', '1537:EventType.VlmMediaRemoved', '1538:EventType.VlmMediaChanged']
	media['items'] = {}
	media_dict = media['items']
	if play_type == 'series' or play_type == 'videos':
		media_dict['series'] = {}
		media_dict = media_dict['series']
		if rows == None:
			rows = querydb(table='series', column='id,series_name,tmdbid,season,episode_number,episode_name,description,air_date,still_path,filepath', query='isactive = 1')
		for _id, series_name, tmdbid, season, episode_number, episode_name, description, air_date, still_path, filepath in rows:
			if ':' in episode_name:
				chunks = episode_name.split(':')
				j = '|'
				episode_name = j.join(chunks)
			string = ("series:" + series_name + ":" + str(season) + ":" + str(episode_number) + ":" + episode_name + ":" + str(_id))
			media['DBMGR_RESULTS'].append(string)
			media_dict[_id] = {}
			dic = media_dict[_id]
			dic['type'] = 'series'
			dic['series_name'] = series_name
			dic['tmdbid'] = tmdbid
			dic['season'] = season
			dic['episode_number'] = episode_number
			dic['episode_name'] = episode_name
			dic['description'] = description
			dic['air_date'] = air_date
			dic['still_path'] = still_path
			dic['filepath'] = filepath
	if play_type == 'movies' or play_type == 'videos':
		media_dict['movies'] = {}
		media_dict = media_dict['movies']
		rows = querydb(table='movies', column='id,tmdbid,title,year,release_date,description,poster,filepath', query='isactive = 1')
		for _id, tmdbid, title, year, release_date, description, poster, filepath in rows:
			string = ("movies:" + title + ":" + str(year) + ":" + str(_id))
			media['DBMGR_RESULTS'].append(string)
			media_dict[_id] = {}
			dic = media_dict[_id]
			dic['type'] = 'movies'
			dic['tmdbid'] = tmdbid
			dic['title'] = title
			dic['year'] = year
			dic['release_date'] = release_date
			dic['description'] = description
			dic['poster'] = poster
			dic['filepath'] = filepath
	if play_type == 'music':
		media_dict['music'] = {}
		media_dict = media_dict['music']
		rows = querydb(table = 'music', column='id,title,accoustic_id,album,album_id,artist_id,year,artist,track,track_ct,filepath', query='isactive = 1')
		for _id, title, accoustic_id, album, album_id, artist_id, year, artist, track, track_ct, filepath in rows:
			string = ("music:" + str(artist) + ":" + str(title) + ":" + str(album) + ":" + str(year) + ":" + str(track) + ":" + str(_id))
			media['DBMGR_RESULTS'].append(string)
			media_dict[_id] = {}
			dic = media_dict[_id]
			dic['type'] = 'music'
			dic['title'] = title
			dic['accoustic_id'] = None
			dic['album'] = album
			dic['album_id'] = album_id
			dic['artist_id'] = artist_id
			dic['year'] = year
			dic['artist'] = artist
			dic['track'] = track
			dic['track_ct'] = track_ct
			dic['filepath'] = filepath
	return media


def file_browse_window():
	x = conf['windows']['browser']['x']
	y = conf['windows']['browser']['y']
	w = conf['windows']['browser']['w']
	h = conf['windows']['browser']['h']
	filepath = None
	file_browser_layout = [[sg.T("")], [sg.Text("Choose a file: "), sg.Input(), sg.FileBrowse(key="-IN-")],[sg.Button("Submit")]]
	file_browser_window = sg.Window('Load Media file or playlist...', file_browser_layout, location=(int(x), int(y)), size=(int(w), int(h)))
	while True:
		file_browser_event, file_browser_values = file_browser_window.read()
		if file_browser_event == sg.WIN_CLOSED or file_browser_event=="Exit":
			filepath = None
			break
		elif file_browser_event == "Submit":
			filepath = file_browser_values["-IN-"]
			file_browser_window.close()
			break
	#print ("filepath (gui):", filepath)
	return filepath


def folder_browse_window():
	x = conf['windows']['browser']['x']
	y = conf['windows']['browser']['y']
	w = conf['windows']['browser']['w']
	h = conf['windows']['browser']['h']
	path = None
	folder_browser_layout = [[sg.T("")], [sg.Text("Choose directory: "), sg.Input(), sg.FolderBrowse(key="-SAVE_PATH-")], sg.Button("Submit")]
	folder_browser_window = sg.Window("Save playlist file...", folder_browser_layout, location=(int(x), int(y)), size=(int(w), int(h)))
	while True:
		folder_browser_event, folder_browser_values = folder_browser_window.read()
		if folder_browser_event == sg.WIN_CLOSED or folder_browser_event=="Exit":
			path = None
			break
		elif folder_browser_event == "Submit":
			path = folder_browser_values["-IN-"]
			folder_browser_window.close()
			break
	j = ' '
	s2 = 'file://'
	path = j.join(path.split(s)).split(s2)[1]
	return path


def set_media_paths():
	conf = readConf()
	np.log("Starting interactive directory setup...", 'info')
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
		np.writeConf(conf)
		np.log("Media directories configured! Continuing...", 'info')

