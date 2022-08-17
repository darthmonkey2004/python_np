import datetime
import PySimpleGUI as sg
import requests
import logging
import vlc
import pickle
import os
import inspect
import subprocess
from np.core.log import np_logger
from np.core.conf import readConf, writeConf, initConf
log = np_logger().log_msg

from np.utils.xrandr import xrandr
import pickle
from videoprops import get_video_properties
from np.core.nplayer_db import querydb
import os
home = os.path.expanduser("~")
DATA_DIR = (home + os.path.sep + ".np")
global LOGFILE, CONFFILE
LOGFILE = f"{DATA_DIR}/nplayer.log"
CONFFILE = f"{DATA_DIR}/nplayer.conf"
mk_conf = False


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


conf = readConf()




class err():
	def __init__(self):
		self.log = log
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
		print ("Exception in core.py, read_history, line 223:", e)
	return history_dict


def write_history(history_dict):
	try:
		with open (history_file, 'wb') as f:
			pickle.dump(history_dict, f)
		f.close()
		return True
	except Exception as e:
		print ("Exception in core.py, write_history, line 234:", e)
		return False


def set_play_type(play_type):
	play_type = play_type
	conf['play_type'] = play_type
	writeConf(conf)
	np.log('core.py, set_play_type: Conf file written!', 'info')


def calculate_scale(_file, conf=None, _type='file'):
	if _file == None:
		return 0
	log(f"ACTION:calculate_scale, file='{_file}', type='{type(_file)}'", 'info')
	if _type != 'file':
		print ("type is not file, cannot calculate scale:", _type)
		return False
	if conf == None:
		conf = readConf()
	if not os.path.exists(_file):
		print ("File not found:,", _file)
		return False
	try:
		vw, vh = get_res(_file)
	except Exception as e:
		log(f"Exception in core.py, calculate_scale:{e}", 'error')
		vw, vh = 1024, 768
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
	conf = readConf()
	data = xrandr()
	state = 'visible'
	viewer_screen = conf['screen']
	log('core.py.init_window_position running from somewhere...', 'info')
	conf['windows'] ={}
	conf['windows']['viewer'] = {}
	conf['windows']['viewer'][0] = {}
	conf['windows']['viewer'][1] = {}
	conf['windows']['viewer'][0]['x'] = data[0]['pos_x']
	conf['windows']['viewer'][0]['y'] = data[0]['pos_y']
	conf['windows']['viewer'][0]['w'] = data[0]['w']
	conf['windows']['viewer'][0]['h'] = data[0]['h']
	conf['windows']['viewer'][1]['x'] = data[1]['pos_x']
	conf['windows']['viewer'][1]['y'] = data[1]['pos_y']
	conf['windows']['viewer'][1]['w'] = data[1]['w']
	conf['windows']['viewer'][1]['h'] = data[1]['h']
	conf['windows']['gui'] = {}
	conf['windows']['pbdl'] = {}
	conf['windows']['pbdl_dl'] = {}
	conf['windows']['ytdl'] = {}
	conf['windows']['browser'] = {}
	conf['windows']['gui']['hidden'] = {}
	conf['windows']['gui']['visible'] = {}
	conf['windows']['gui']['hidden'][0] = {}
	conf['windows']['gui']['visible'][0] = {}
	conf['windows']['gui']['hidden'][1] = {}
	conf['windows']['gui']['visible'][1] = {}
	x0, y0 = data[0]['pos_x'], data[0]['pos_y']
	x1, y1 = data[1]['pos_x'], data[1]['pos_y']
	conf['windows']['gui']['visible'][0]['x'] = x0
	conf['windows']['gui']['visible'][0]['y'] = y0
	conf['windows']['gui']['visible'][1]['x'] = x1
	conf['windows']['gui']['visible'][1]['y'] = y1
	conf['windows']['gui']['visible'][0]['w'] = 1024
	conf['windows']['gui']['visible'][0]['h'] = 600
	conf['windows']['gui']['visible'][1]['w'] = 1024
	conf['windows']['gui']['visible'][1]['h'] = 600
	conf['windows']['gui']['hidden'][0]['x'] = x1
	conf['windows']['gui']['hidden'][0]['y'] = y1
	conf['windows']['gui']['hidden'][1]['x'] = x0
	conf['windows']['gui']['hidden'][1]['y'] = y0
	conf['windows']['gui']['hidden'][0]['w'] = 1024
	conf['windows']['gui']['hidden'][0]['h'] = 600
	conf['windows']['gui']['hidden'][1]['w'] = 1024
	conf['windows']['gui']['hidden'][1]['h'] = 600
	conf['windows']['browser'] = {}
	conf['windows']['browser']['w'] = 600
	conf['windows']['browser']['h'] = 150
	screen = conf['screen']
	if screen == 0:
		screen = 1
	elif screen == 1:
		screen = 0
	x, y = conf['screens'][screen]['pos_x'], conf['screens'][screen]['pos_y']
	conf['windows']['browser']['x'] = x
	conf['windows']['browser']['y'] = y
	conf['windows']['pbdl'] = {}
	conf['windows']['pbdl']['w'] = 900
	conf['windows']['pbdl']['h'] = 900
	conf['windows']['pbdl']['x'] = x
	conf['windows']['pbdl']['y'] = y
	conf['windows']['pbdl_dl'] = {}
	conf['windows']['pbdl_dl']['w'] = 600
	conf['windows']['pbdl_dl']['h'] = 300
	conf['windows']['pbdl_dl']['x'] = x
	conf['windows']['pbdl_dl']['y'] = y
	conf['windows']['ytdl'] = {}
	conf['windows']['ytdl']['w'] = 750
	conf['windows']['ytdl']['h'] = 300
	conf['windows']['ytdl']['x'] = x
	conf['windows']['ytdl']['y'] = y
	conf['windows']['is_default'] = True
	conf['windows']['gui']['visible_status'] = 'visible'
	writeConf(conf)
	return conf['windows']


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
		
		rows = querydb(table = 'music', column='id,title,artist', query='isactive = 1')
		for _id, title, artist in rows:
			string = (f"music:{artist}:{title}:{_id}")
			media['DBMGR_RESULTS'].append(string)
			media_dict[_id] = {}
			dic = media_dict[_id]
			dic['type'] = 'music'
			dic['title'] = title
			dic['artist'] = artist
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
	folder_browser_layout = [[sg.T("")], [sg.Text("Choose directory: "), sg.Input(), sg.FolderBrowse(key="-SAVE_PATH-")], [sg.Button("Submit")]]
	folder_browser_window = sg.Window("Save playlist file...", folder_browser_layout, location=(int(x), int(y)), size=(int(w), int(h)))
	while True:
		folder_browser_event, folder_browser_values = folder_browser_window.read()
		if folder_browser_event == sg.WIN_CLOSED or folder_browser_event=="Exit":
			path = None
			return None
		elif folder_browser_event == "Submit":
			path = folder_browser_values["-SAVE_PATH-"]
			folder_browser_window.close()
			return path

