#!/usr/bin/python3
from np.core.core import shell, get_version, match_repo_version
import np
from np.utils.pbdl.pbdl import start as start_pbdl
from np.utils.pbdl.pbdl import pbdl
from np.utils.cleandb import run as cleandb
from np.core.gui import folder_browse_window, file_browse_window
from threading import *
import queue
import timeit
import urllib.parse
import PySimpleGUI as sg
import os
import subprocess
querydb = np.querydb
xrandr = np.xrandr
import pickle
import vlc
import time
import sys
from np.core.log import np_logger
from np.ws.server import server
log = np_logger().log_msg
update_ct = 5
remote_com_q = queue.Queue()
remote_ret_q = queue.Queue()
server = server(remote_com_q, remote_ret_q)
pbdl = pbdl()
VLC_VIDEO_FILTERS = ['video:adjust', 'video:alphamask', 'video:anaglyph', 'video:antiflicker', 'video:audiobargraph_v', 'video:ball', 'video:blendbench', 'video:bluescreen', 'video:canvas', 'video:chain', 'video:colorthres', 'video:croppadd', 'video:deinterlace', 'video:edgedetection', 'video:erase', 'video:extract', 'video:fps', 'video:freeze', 'video:gaussianblur', 'video:gradfun', 'video:gradient', 'video:grain', 'video:hqdn3d', 'video:invert', 'video:logo', 'video:magnify', 'video:mirror', 'video:motionblur', 'video:motiondetect', 'video:oldmovie', 'video:posterize', 'video:postproc', 'video:psychedelic', 'video:puzzle', 'video:ripple', 'video:rotate', 'video:scene', 'video:sepia', 'video:sharpen', 'video:transform', 'video:vaapi_filters', 'video:vaapi_filters', 'video:vaapi_filters', 'video:vaapi_filters', 'video:vaapi_filters', 'video:vdpau_adjust', 'video:vdpau_deinterlace', 'video:vdpau_sharpen', 'video:vhs', 'video:wave']
VLC_AUDIO_FILTERS = ['audio:audiobargraph_a', 'audio:chorus_flanger', 'audio:compressor', 'audio:equalizer', 'audio:gain', 'audio:headphone', 'audio:karaoke', 'audio:mono', 'audio:normvol', 'audio:param_eq', 'audio:remap', 'audio:scaletempo', 'audio:scaletempo_pitch', 'audio:spatialaudio', 'audio:spatializer', 'audio:stereo_widen']


def run_server():
	global server
	try:
		server_thread = Thread(target=server.start)
		server_thread.setDaemon(True)
		server_thread.start()
		log(f"Socket server started!", 'info')
	except Exception as e:
		log(f"Error starting socket server: {e}", 'error')

def sqlite3(query):
	dbfile = (f"{np.DATA_DIR}{os.path.sep}nplayer.db")
	com = (f"sqlite3 '{dbfile}' \"{query}\"")
	out = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	if MP.conf['debug'] == True:
		log(f"SQLITE3 Query: {query}", 'info')
		log(f"SQLITE3 Results: {out}", 'info')
	return out

def lookup_series(series_name, season, episode_number):
	return np.rt_series_query(series_name, season, episode_number)

def lookup_movies(title):
	return np.rt_movies_query(title)



def get_media(table=None, isactive=1):
	if table == None:
		table = MP.conf['play_type']
	query_string = (f"select filepath from {table} where isactive = {isactive};")
	return sqlite3(query_string)
					

def recenter_ui():
	viewer_screen = MP.conf['screen']
	if viewer_screen == 0:
		gui_screen = 1
	elif viewer_screen == 1:
		gui_screen = 0
	else:
		gui_screen = 0
	try:
		state = 'visible'
		gui_x = int(MP.conf['windows'][gui_screen]['gui']['x'])
		gui_y = int(MP.conf['windows'][gui_screen]['gui']['y'])
		UI.WINDOW.move(gui_x, gui_y)
		UI.WINDOW2.move(int(MP.conf['windows'][viewer_screen]['viewer']['x']), int(MP.conf['windows'][viewer_screen]['viewer']['y']))
		np.writeConf(MP.conf)
	except:
		try:
			test = MP.conf['windows']
		except Exception as e:
			MP.conf['windows'] = np.init_window_position()
			log(f"init_window_position running from 'recenter_ui', np_main.py, MP.conf['windows'] not initialized ({e})", 'warning')
			
		gui_x = int(MP.conf['windows'][gui_screen]['gui']['x'])
		gui_y = int(MP.conf['windows'][gui_screen]['gui']['y'])
		UI.WINDOW.move(gui_x, gui_y)
		screen = int(MP.conf['screen'])
		UI.WINDOW2.move(int(MP.conf['windows'][viewer_screen]['viewer']['x']), int(MP.conf['windows'][viewer_screen]['viewer']['y']))
		np.writeConf(MP.conf)

def dbmgr_add_items(items=None):
	if items == None:
		items = UI.window['-DBMGR_SELECTED_ROWS-']
	all_items = UI.uivalues['-PLAYLIST_ITEMS-']
	for add in items:
		if add not in items:
			MP.dbmgr_picked_items.append(add)
	MP.dbmgr_picked_items = items
	UI.WINDOW['-DBMGR_SELECTED_ROWS-'].update(MP.dbmgr_picked_items)
	return MP.dbmgr_picked_items


def dbmgr_remove_items(items=None):
	if items == None:
		items = UI.window['-DBMGR_SELECTED_ROWS-']
	all_items = UI.uivalues['-PLAYLIST_ITEMS-']
	for rm in items:
		if rm in all_items:
			all_items.remove(rm)
	MP.dbmgr_picked_items = items
	UI.WINDOW['-DBMGR_SELECTED_ROWS-'].update(MP.dbmgr_picked_items)
	return MP.dbmgr_picked_items

def dbmgr_clear_all():
	MP.dbmgr_picked_items = []
	UI.WINDOW['-DBMGR_SELECTED_ROWS-'].update(MP.dbmgr_picked_items)


def dbmgr_select_all():
	MP.dbmgr_picked_items = sorted(MP.playlist)
	UI.WINDOW['-DBMGR_SELECTED_ROWS-'].update(MP.dbmgr_picked_items)


def store_window_location():
	MP.conf = np.readConf()
	try:
		viewer_screen = MP.conf['screen']
		if viewer_screen == 0:
			gui_screen = 1
		elif viewer_screen == 1:
			gui_screen = 0
		else:
			gui_screen = 0
		MP.conf['windows'][gui_screen]['gui']['x'], MP.conf['windows'][gui_screen]['gui']['y'] = UI.get_window_location('gui')
		np.writeConf(MP.conf)
		log(f"Window location stored:{MP.conf['windows'][gui_screen]['gui']['x']}, {MP.conf['windows'][gui_screen]['gui']['y']}", 'info')
	except Exception as e:
		log(f"Unable to get window location (probably closed). Details: {e}", 'error')

def gui_reset():
	global P, MP, UI
	MP.conf['GUI_RESET'] = True
	log(f"Reset Starting (Reset set to true)! Conf updated!.", 'info')
	np.writeConf(MP.conf)
	update_resume()
	MP.stop()
	UI.WINDOW.close()
	UI.WINDOW2.close()

def set_video_out():
	global MP, UI, P
	if MP.conf['video_player'] == 'vlc':
		if UI.win_type == 'internal':
			P.set_xwindow(UI.WINDOW2['-VID_OUT-'].Widget.winfo_id())


def change_filter(f):#sets audio filters to vlc instance. returns true on success, false on fail.
	if ':' in f:
		t = f.split(':')[0]
		f = f.split(':')[1]
	if f in MP.conf['vlc']['opts']:
		a = 'remove'
	else:
		a = 'add'
	P.stop()
	P.release()
	if t == 'audio':
		f_string = ("--audio-filter=" + f)
	elif t == 'video':
		f_string = ("--video-filter=" + f)
	else:
		txt = ("Unknown type:" + t + ", Available: 'audio', 'video'")
		np.log(txt, 'info')
		return False
	if a == 'add':
		try:
			MP.conf = np.readConf()
			current_opts = MP.conf['vlc']['opts']
			opts = (current_opts + " " + f_string)
			MP.conf['vlc']['opts'] = opts
			np.log(f"Updated audio filter options:{opts}", 'info')
		except Exception as e:
			np.log(f"Failed to set audio filter option:, {e}, {f}, {MP.conf['vlc']['opts']}", 'error')
			return False
	elif a == 'remove':
		try:
			MP.conf = np.readConf()
			current_opts = MP.conf['vlc']['opts']
			s = " "
			_list = current_opts.split(s)
			_list.remove(f_string)
			j = ' '
			MP.conf['vlc']['opts'] = j.join(_list)
			np.log("Updated video filter options:{MP.conf['vlc']['opts']}", 'info')
		except Exception as e:
			np.log("Failed to remove video filter option:, {e}, {f}, {MP.conf['vlc']['opts']}", 'error')
			return False
	else:
		txt = ("Unknown action:" + a + ", Available: 'add', 'remove'")
		np.log(txt, 'warning')
		return False
	gui_reset()


def rotate(deg):
	if MP.conf['nowplaying']['filepath'] is not None:
		filepath = MP.conf['nowplaying']['filepath']
	else:
		play_file = P.get_media().get_mrl().split("file://")[1]
		filepath = urllib.parse.unquote(play_file)
	if MP.conf['nowplaying']['play_pos'] is not None and MP.conf['nowplaying']['play_pos'] != 0:
		pos = float(MP.conf['nowplaying']['play_pos'])
	else:
		pos = P.get_position()
	P.stop()
	P.release()
	if MP.conf['rotate'] >= 270:
		MP.conf['rotate'] = 0
		opt=("--no-xlib")
	elif MP.conf['rotate'] < 0:
		MP.conf['rotate'] = 0
		opt=("--no-xlib")
	else:
		MP.conf['rotate'] = MP.conf['rotate'] + deg
		deg = str(MP.conf['rotate'])
		opt=("--no-xlib --video-filter=transform{type=" + deg + "}")
	MP.conf['vlc']['opts'] = opt
	gui_reset()


def update_resume():
	s='%20'
	j = ' '
	s2 = 'file://'
	filepath = P.get_media().get_mrl().split("file://")[1]
	MP.conf['nowplaying']['filepath'] = urllib.parse.unquote(filepath)
	MP.conf['nowplaying']['play_pos'] = P.get_position()
	log(f"np_main.py, update_resume: modified conf with play_pos and now_playing: play_pos={MP.conf['nowplaying']['play_pos']}, now_playing={MP.conf['nowplaying']['filepath']}, Play Type:{MP.conf['play_type']}", 'info')
	np.writeConf(MP.conf)



def playlist_click(_id, table):
	query_string = ("id = " + str(_id))
	_file = np.querydb(table, 'filepath', query_string)[0][0]
	if MP.conf['debug'] == True:
		np.log(f"{MP.history['history']}", 'info')
	MP.play(_file)


def update_media_info(row):
	if MP.conf['debug'] == True:
		log(f"Media Info update function entered. Data: {row}", 'debug')
	row = MP.dbmgr_picked_items
	row = row.split(':')
	if 'fart' == True:
		table = row[0]
		_id = row[5]
		query_string = ("id = " + str(_id))
		results = np.querydb(table='series', column='id,isactive,series_name,tmdbid,season,episode_number,episode_name,description,air_date,still_path,duration,filepath,md5,url', query=query_string)[0]
		if MP.conf['play_type'] == 'movies':
			columns_list = ['id', 'isactive', 'tmdbid', 'title', 'year', 'release_date', 'duration', 'description', 'poster', 'filepath', 'md5', 'url']
		elif MP.conf['play_type'] == 'series' or MP.conf['play_type'] == 'videos':
			columns_list = ['id', 'isactive', 'series_name', 'tmdbid', 'season', 'episode_number', 'episode_name', 'description', 'air_date', 'still_path', 'duration', 'filepath', 'md5', 'url']
		elif MP.conf['play_type'] == 'music':
			columns_list = ['id', 'isactive', 'title', 'accoustic_id', 'album', 'album_id', 'artist_id', 'year', 'artist', 'track', 'track_ct', 'filepath']
		pos = -1
		selected_data = {}
		for column in columns_list:
			pos = pos + 1
			val = results[pos]
			if column == 'filepath':
				filepath = val
			key = ("-" + str(column) + "-")
			selected_data[key] = val
			UI.WINDOW[key].update(val)


def load_playlist(filepath=None):
	if filepath is None:
		log(f"Error: Cartoons can be quite distracting, ergo you didn't give me a path to load. You're forgiven.", 'error')
		MP.play_mode = 'database'
		UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
		MP.play(filepath)
	else:
		if ".txt" in filepath:
			MP.playlist = sorted(MP.load_playlist(filepath))
			UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.playlist)
			MP.play_mode = 'playlist'
			UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
			filepath = MP.playlist[0]
			MP.play(filepath)
		else:
			MP.play_mode = 'database'
			UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
			MP.play(filepath)


def set_debug(mode=None):
	if mode == None:
		debug = MP.conf['debug']
		if debug == True:
			debug = False
		elif debug == False:
			debug = True
	else:
		debug = mode
	MP.conf['debug'] = debug
	np.writeConf(MP.conf)
	log(f"Debug option changed: {MP.conf['debug']}!", 'info')



def remote_handler(com, arg):
	global server
	remote_commands = ['create_viewer', 'help', 'commands', 'play', 'create_gui', 'close_gui', 'close_viewer', 'pause', 'stop', 'skip_next', 'skip_prev', 'vol_set', 'vol_up', 'vol_down', 'mute', 'unmute', 'quit', 'load', 'play_mode', 'play_type', 'seek', 'move_gui', 'move_player', 'get_pos', 'get_window_location', 'media_pick', 'media_get', 'debug']
	global P, MP, UI
	log(f"Command: '{com}', Argument: '{arg}'", 'info')
	ret = None
	if com == 'play':					
		MP.play()
		ret = "REMOTE: Playing!"
		log("REMOTE: Playing!", 'info')
	elif com == 'lookup_movies':
		ret = lookup_movies(arg)
		log(f"REMOTE:MovieLookup={ret}", 'info')
	elif com == 'bring_to_front':
		if arg == None:
			np.bring_to_front(UI.WINDOW)
		else:
			for win in UI.windows.values():
				if arg == win.Title:
					np.bring_to_front(win)
		ret = "Moved to front!"
	elif com == 'send_to_back':
		if arg == None:
			np.send_to_back(UI.WINDOW)
		else:
			for win in UI.windows.values():
				if arg == win.Title:
					np.send_to_back(win)
		ret = "Sent to back!"
	elif com == 'write_event':
		try:
			event, value, win = arg.split(':')
			if win == None:
				win = UI.WINDOW
				write_event(event, value, win)
		except:
			np.log(f"Unable to parse string! Expected event,value,win..", 'error')
		ret = "Event written!"
	elif com == 'restore':
		if arg is None:
			win = UI.WINDOW
		win.restore()
		log(f"{win.Title} restored!", 'info')
		ret = 'Window restored!'
	elif com == 'maximize':
		if arg is None:
			win = UI.WINDOW
		win.maximize()
		log(f"{win.Title} maximized!", 'info')
		ret = 'Window Maximized!'
	elif com == 'hide':
		if arg is None:
			win = UI.WINDOW
		win.hide()
		log(f"{win.Title} hidden!", 'info')
		ret = 'Window hidden!'
	elif com == 'un_hide':
		if arg is None:
			win = UI.WINDOW
		win.un_hide()
		log(f"{win.Title} revealed!", 'info')
		ret = 'Window unhidden!'
	elif com == 'reappear':
		if arg is None:
			win = UI.WINDOW
		win.reappear()
		log(f"{win.Title} reappeared!", 'info')
		ret = 'Window reappeared!'
	elif com == 'dissapear':
		if arg is None:
			win = UI.WINDOW
		win.dissapear()
		log(f"{win.Title} dissapeared!", 'info')
		ret = 'Window disappeared!'
	elif com == 'get_pointer':
		if arg is None:
			win = UI.WINDOW
		coords = win.get_pointer()
		log(f"REMOTE:get_pointer={coords}", 'info')
		ret = f"Mouse coords: {coords}"
	elif com == 'lookup_series':
		try:
			sn, s, e = arg.split(',')
		except Exception as e:
			log(f"REMOTE:Error: Need Name, season and episode. Got {arg}. Errmsg = {e}", 'info')
			return None
		ret = lookup_series(sn, s, e)
		log(f"REMOTE:SeriesLookup={ret}", 'info')
	elif com == 'recenter_ui':
		recenter_ui()
		ret = 'ui recentered!'
	elif com == 'help' or com == 'commands':
		com = f"filepath=$(which np); cat \"$filepath\""
		code = np.shell(com).split("def remote_handler(com, arg):")[1].split('return True')[0].split("\n")
		coms = []
		for line in code:
			if 'com == ' in line:
				com = line.split(' == ')[1].split(':')[0].split("'")[1]
				coms.append(com)
		j = ", "
		ret = j.join(coms)
		log(f"REMOTE: Commands List: {ret}", 'info')
	elif com == 'create_gui':
		UI.WINDOW = UI.create_gui_window()
		recenter_ui()
		log("REMOTE:GUI Window created.", 'info')
		ret = 'gui created!'
	elif com == 'close_gui':
		title = UI.WINDOW.Title
		if title in UI.windows:
			UI.windows.remove(title)
			np.log("REMOTE: Closed gui (removed from active windows list)", 'info')
		UI.WINDOW.close()
		log("REMOTE:GUI Window closed.", 'info')
		ret = 'gui closed!'
	elif com == 'pause':
		P.pause()
		log("REMOTE: Paused", 'info')
		ret = 'paused'
	elif com == 'stop':
		MP.stop()
		log("REMOTE: Stopped", 'info')
		ret = 'stopped'
	elif com == 'skip_next':
		MP.skip_next()
		log("REMOTE: Skipped Next", 'info')
		ret = 'skipped next'
	elif com == 'skip_prev':
		MP.skip_previous()
		log("REMOTE: Skipped Previous", 'info')
		ret = 'skipped previous'
	elif com == 'vol_set':
		MP.volume_set(arg)
		log(f"REMOTE: vol_set={arg}", 'info')
		ret = f'volume set: {arg}'
	elif com == 'vol_up':
		log("REMOTE: volume_up", 'info')
		MP.volume_up()
		ret = 'volume up'
	elif com == 'vol_down':
		MP.volume_down()
		log("REMOTE: volume_down", 'info')
		ret = 'volume down'
	elif com == 'mute':
		MP.volume_set(0)
		log("REMOTE: Mute", 'info')
		ret = 'Muted!'
	elif com == 'unmute':
		vol = int(self.conf['volume'])
		MP.volume_set(vol)
		log("REMOTE: Unmuted", 'info')
		ret = 'Unmuted'
	elif com == 'quit':
		log("REMOTE: Quitting...", 'info')
		update_resume()
		MP.exit = True
		ret = 'Quittin time..'
	elif com == 'load':
		log(f"REMOTE: Loading file:{arg}", 'info')
		load_playlist(arg)
		ret = f"File loaded: {arg}"
	elif com == 'play_mode':
		MP.play_mode = arg
		log(f"REMOTE: Play mode set:{arg}", 'info')
		ret = f"Play mode set: {arg}"
	elif com == 'play_type':
		MP.conf['play_type'] = arg
		np.writeConf(MP.conf)
		MP.play_type = arg
		log(f"REMOTE: Play type set:{arg}", 'info')
		gui_reset()
		ret = f"Play type set: {arg}"
	elif com == 'seek':
		pos = float(float(arg) / 100)
		P.set_position(pos)
		log(f"REMOTE: seek to position:{pos}", 'info')
		ret = f"Seek to position: {pos}"
	elif com == 'move_gui':
		x, y = int(arg.split(',')[0]), int(arg.split(',')[1])
		UI.move_window('gui', x, y)
		log(f"REMOTE: GUI Window moved by remote: ({x},{y})", 'info')
		ret = f"Moved gui window: ({x}, {y})"
	elif com == 'move_player':
		x, y = int(arg.split(',')[0]), int(arg.split(',')[1])
		UI.move_window('player', x, y)
		log(f"REMOTE: Player Window moved by remote: ({x},{y})", 'info')
		ret = f"Moved viewer window: ({x}, {y})"
	elif com == 'get_pos':
		pos = MP.get_position()
		log(f"PLAYBACK_POSITION={pos}", 'info')
		ret = f"Window position (x, y): {pos}"
	elif com == 'get_window_location':
		loc = UI.get_window_location(arg)
		log(f"REMOTE: GUI Window Location={loc}", 'info')
		ret = f"Window location (x, y): {loc}"
	elif com == 'media_pick':
		try:
			if ':' in arg:
				arg = arg.split(':')[1]
			MP.next = arg
			MP.play(MP.next)
			ret = "Playing file: {MP.next}"
			log(f"REMOTE: Playback started. File='{MP.next}'", 'info')
		except Exception as e:
			log(f"REMOTE: Failed to play file:{arg}, Details:{e}", 'error')
			ret = "Pick file failed! ({arg}): {e}"
			return False
	elif com == 'media_get':
		if arg is None:
			files = get_media(arg)
		else:
			files = get_media()
		pos = -1
		l = []
		for filepath in files:
			pos += 1
			string = f"{pos}:{filepath}"
			l.append(string)
		j = "|"
		l = j.join(l)
		log(f"REMOTE: MEDIA_FILES={l}", 'info')
		MP.remote_media = l
		ret = l
	elif com == 'fix_scaling':
		MP.set_scale(MP.conf['nowplaying']['filepath'])
		log("REMOTE: Fix Scaling command received, scale set ({MP.scale})", 'info')
		ret = "Scaling fixed!"
	elif com == 'debug':
		try:
			debug = bool(arg)
			set_debug(debug)
			log(f"REMOTE: Debug value set: {debug}", 'info')
		except Exception as e:
			log(f"REMOTE: Failed to set debug mode: {e}", 'error')
			return False
	server.ret_q.put(ret)
	return True


def refresh_log_data():
	log_data = []
	log_file = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.log')
	with open(log_file, 'r') as f:
		data = f.read().split("\n")
	f.close()
	if data is not None:
		for line in data:
			try:
				add = line.split('--')[1]
			except:
				add = line
			log_data.append(add)
		j = "\n"
		log_data = j.join(log_data)
	else:
		log_data.append('Log is empty!')
	try:
		UI.WINDOW['-DEBUGGER-'].update(log_data)
	except:
		pass


def start():
	global server, remote_q, pbdl
	if os.path.exists('todo.txt'):
		with open('todo.txt', 'r') as f:
			text = f.read()
		f.close()
		print(f"TODO:\n{text}")
	global P, MP, UI, conf, update_ct
	update = 0
	conf = None
	btn = None
	MP = np.nplayer()
	P = MP.init_vlc()
	playlist = np.create_media()
	tab = '-player_control_layout-'
	MP.conf = np.readConf()
	try:
		DEBUG = MP.conf['debug']
	except:
		MP.conf['debug'] = False
	if MP.conf is None:
		np.log("conf is None, re-initializing...", 'warning')
		MP.conf = np.initConf()
		np.log("Defaults restored.", 'info')
		MP.conf['screens'] = xrandr()
	screen = MP.conf['screen']
	try:
		MP.series_history = np.read_history()
	except Exception as e:
		np.log(f"Series history is empty or couldn't read pickle data: line 557, {e}", 'error')
		MP.series_history = {}
	if MP.conf['network_mode']['media_mode'] == 'local':
		try:
			media_dirs = MP.conf['media_directories']
			log("Media directories found in conf!", 'info')
		except Exception as e:
			log("Error: media directories not found inf conf file:{e}", 'error')
			np.set_media_paths()
	UI = np.gui()
	log("UI created: np_main.py, Start, line 694", 'info')
	UI.WINDOW.read(timeout=1)
	MP.viewer_win_w, MP.viewer_win_h = UI.WINDOW.get_screen_size()
	try:
		init = MP.conf['init']
	except Exception as e:
		np.log(f"Exception in UI: {e}", 'warning')
		MP.conf['init'] = True
		try:
			test = MP.conf['windows']
		except Exception as e:
			MP.conf['windows'] = np.init_window_position()
			log(f"init_window_position running from 'start', np_main.py, MP.conf['init'] != True, {e}", 'warning')
		np.writeConf(MP.conf)
		ui_center()
	set_video_out()
	MP.continuous = 1
	input_enabled = 0
	btn = None
	evque = []
	readct = 0
	readmax = 1500
	if MP.conf['remote']['server']['state'] == 1:
		run_server()
	recenter_ui()
	MP.version = get_version()
	MP.update_needed = match_repo_version()
	log(f"Starting nplayer (V{MP.version})...", 'info')
	while True:
		readct += 1
		start_timer = timeit.default_timer()
		data = None
		update = update + 1
		#Check remote queue for input commands from np.remote
		if update >= update_ct or update == 0:
			try:
				if not remote_com_q.empty():
					data = remote_com_q.get_nowait()
				if data is not None and data != '':
					log(f"Command received: '{data}'", 'info')
					if '=' in data:
						com = data.split('=')[0]
						try:
							arg = data.split('=')[1]
							log(f"Com: {com}, Arg: {arg}", 'info')
							remote_handler(com, arg)
							
						except Exception as e:
							arg = None
							log(f"Com: {com}, Arg: None", 'error')
							remote_handler(com, arg)
						# if command received via socket server (from np.remote), pass to handler.
					else:
						com = data
						arg = None
						remote_handler(com, arg)
			except Exception as e:
				log(f"Exception receiving remote command: '{e}'", 'error')
				
			UI.window, UI.uievent, UI.uivalues = UI.get_events()
			if UI.uievent is not None and UI.uievent != '__TIMEOUT__':
				needspacer = 1
				event = UI.uievent
				if UI.uivalues is not None:
					values = UI.uivalues
				if MP.conf['debug'] == True:
					log(f"EVENT_HANDLER_DEBUG=TRUE: event={event}", 'info')
				if event == '-MEDIA_MODE-':
					media_mode = values[event]
					if media_mode == 'remote':
						if media_host is None:
							media_host = UI.get_user_input('Please enter remote ip:' )
						if media_user is None:
							media_user = UI.get_user_input('Please enter remote username: ')
					MP.conf['network_mode']['media_mode'] = media_mode
					MP.conf['network_mode']['media_host'] = media_host
					MP.conf['network_mode']['media_user'] = media_user
					np.writeConf(MP.conf)
					log(f"Network media mode changed:{media_mode}", 'info')
				elif event == 'Hide UI':
					title = UI.WINDOW.Title
					if title in UI.windows:
						UI.windows.remove(title)
						np.log("REMOTE: Closed gui (removed from active windows list)", 'info')
					UI.WINDOW.close()
					log("REMOTE:GUI Window closed.", 'info')
				elif event == '-CONTROL_MODE-':
					control_mode = values[event]
					if media_mode == 'remote':
						conf['network_mode']['control_mode'] = 'remote'
						if conf['network_mode']['control_host'] == None:
							conf['network_mode']['control_host'] = UI.get_user_input('Please enter remote host ip: ')
			
					if control_mode == 'remote':
						if control_host is None:
							control_host = UI.get_user_input('Please enter remote ip:' )
						if control_user is None:
							control_user = UI.get_user_input('Please enter remote username: ')
					np.set_control_mode(control_mode=control_mode, control_host=control_host, control_user=control_user)
					log(f"Network controller mode changed:{control_mode}", 'info')
				elif event == 'Hide UI':
					hide_ui()
					log("EVENT:UI Hidden", 'info')
				elif event == '-Clean Database-':
					cleandb()
				elif event == 'Exit' or event == 'Close':
					update_resume()
					MP.exit = True
					MP.conf['remote']['server']['pid'] = None
					np.writeConf(MP.conf)
					log(f"Exit set to true {event}", 'info')
				elif event == 'store window location':
					store_window_location()
					log("Window location stored!", 'info')
				elif event == '-episode_number-' or event == '-filepath-' or event == '-series_name-' or event == '-season-':
					k = event
					v = values[event]
					MP.target[k] = v
					log(f"set target {k} to {v}", 'info')
				elif event == '-Query TMDB-':
					if MP.target['-series_name-'] is not None and MP.target['-season-'] is not None and MP.target['-episode_number-'] is not None:
						data = np.lookup_series(MP.target['-series_name-'], MP.target['-season-'], MP.target['-episode_number-'])
						if data:
							MP.target['-episode_name-'] = str(data['name'])
							MP.target['-description-'] = str(data['overview'])
							MP.target['-air_date-'] = str(data['air_date'])
							MP.target['-still_path-'] = str(data['still_path'])
							MP.target['-tmdbid-'] = str(data['tmdbid'])
							UI.WINDOW['-episode_name-'].update(MP.target['-episode_name-'])
							UI.WINDOW['-description-'].update(MP.target['-description-'])
							UI.WINDOW['-air_date-'].update(MP.target['-air_date-'])
							UI.WINDOW['-still_path-'].update(MP.target['-still_path-'])
							UI.WINDOW['-tmdbid-'].update(MP.target['-tmdbid-'])
				elif event == '-table_series-' or event == '-table_movies-' or event == '-table_music-':
					if event == '-table_series-':
						table = 'series'
					elif event == '-table_movies-':
						table = 'movies'
					elif event == '-table_music-':
						table = 'music'
					columns = np.get_columns(table)
					UI.WINDOW['-DBMGR_PICKED_COLUMNS-'].update(columns)
				elif event == '-PLAY_TYPE-':
					MP.conf['play_type'] = values[event]
					np.writeConf(conf)
					log(f"Play type changed:{MP.conf['play_type']}", 'info')
					gui_reset()
				elif event == '-setactive-':
					val = values[event]
					if val == False:
						isactive=0
					elif val == True:
						isactive=1
					else:
						isactive=1
				elif event == '-PLAY_POS-':
					val = float(values[event])
					P.set_position(val)
					log(f"UI: Skipped to position {val}", 'info')
				elif event == 'play':
					P.play()
					log(f"ACTION:play", 'info')
				elif event == 'pause':
					P.pause()
					log(f"ACTION:pause", 'info')
				elif event == 'stop':
					P.stop()
					log(f"ACTION:stop", 'info')
				elif event == 'next':
					MP.skip_next()
					log(f"ACTION:skip_next", 'info')
				elif event == 'previous':
					MP.skip_previous()
					log(f"ACTION:skip_previous", 'info')
				elif event == 'rotate 90':
					rotate(90)
					log(f"ACTION:rotate_90", 'info')
				elif event == 'seek fwd':
					MP.seek_fwd()
					log(f"ACTION:seek_fwd", 'info')
				elif event == 'seek rev':
					MP.seek_rev()
					log(f"ACTION:seek_rev", 'info')
				elif event == '-SET_SCREEN-':
					MP.conf['screen'] = int(values[event])
					MP.conf = UI.set_window_screen(MP.conf['screen'])
					np.writeConf(MP.conf)
					log(f"Active screen updated! Needs restart{MP.conf['screen']}", 'info')
					gui_reset()	
				elif event == 'load':
					MP.stop()
					log(f"ACTION:Stop(event=load)", 'info')
					MP.next = values['-VIDEO_LOCATION-']
					log(f"EVENT:next set, {MP.next}", 'info')
					if 'http://' in MP.next or 'https://' in MP.next:
						MP.is_url = True
						if '/home' in MP.next:
							split='https://'
							MP.next = MP.next.split(split)[1]
							MP.next = ('https://' + MP.next)
						v = pafy.new(MP.next)
						stream = v.getbest()
						P = MP.init_vlc(stream.url)
						set_video_out()
						P.play()
						log(f"ACTION:play", 'info')
					else:
						MP.is_url = False
						MP.play(MP.next)
						log(f"ACTION:play", 'info')
				elif event == 'Refresh from Database':
					MP.media = np.create_media()
					UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.playlist)
				elif event == 'Refresh Log Data':
					refresh_log_data()
					readct = 0
				elif event == 'VPN On/Off':
					if VPN == True:
						VPN = False
					elif VPN == False:
						VPN = True
					UI.toggle_vpn()
				elif event == '-CURRENT_PLAYLIST-':
					val = None
					_id = None
					table = None
					if MP.play_mode == 'playlist':
						val = values[event][0]
						if 'series:' in val or 'movies:' in val or 'music:' in val:
							if 'series:' in val:
								_id = val.split(':')[5]
								table = val.split(':')[0]
								playlist_click(_id, table)
							elif 'movies:' in val:
								table = val.split(':')[0]
								title = val.split(':')[1]
								year = val.split(':')[2]
								_id = val.split(':')[3]
								playlist_click(_id, table)
							elif 'music:' in val:
								val = values[event][0]
								_id = val.split(':')[6]
								table = val.split(':')[0]
								playlist_click(_id, table)
						else:
							MP.play(val)
					elif MP.play_mode == 'database':
						if MP.conf['play_type'] == 'series':
							val = values[event][0]
							_id = val.split(':')[5]
							table = val.split(':')[0]
							playlist_click(_id, table)
						elif MP.conf['play_type'] == 'movies':
							try:
								np.log(f"Playlist clicked: {val}")
								val = values[event][0]
								table = val.split(':')[0]
								title = val.split(':')[1]
								year = val.split(':')[2]
								_id = val.split(':')[3]
								playlist_click(_id, table)
							except Exception as e:
								log(f"Error: Movies list is empty! Details:{e}, {val}, {_id}, {table}", 'error')
						elif MP.conf['play_type'] == 'music':
							try:
								val = values[event][0]
								val = val.split(':')
								_id = val[len(val) - 1]
								table = val[0]
								playlist_click(_id, table)
							except Exception as e:
								log(f"Error: List is empty! Details:{e}, {val}, {_id}, {table}", 'error')
				elif event == '-DBMGR_PICKED_COLUMNS-':
					string = None
					if len(values[event]) == 1:
						column = str(values[event][0])
						string = (column + " like '%%'")
						UI.WINDOW['-DBMGR_QUERY_STRING-'].update(string)
					elif len(values[event]) == 0:
						string = "*"
						UI.WINDOW['-DBMGR_QUERY_STRING-'].update(string)
					else:
						for column in values[event]:
							if string == None:
								if column == 'season' or column == 'id' or column == 'isactive' or column == 'episode_number':
									string = (f"{column} = ")
								else:
									string = (f"{column} like '%%'")
							else:
								if column == 'season' or column == 'id' or column == 'isactive' or column == 'episode_number':
									string = (f"{string} and {column} = ")
								else:
									string = (f"{string} and {column} like '%%'")
						UI.WINDOW['-DBMGR_QUERY_STRING-'].update(string)
					UI.WINDOW.refresh()
					if MP.conf['debug'] == True:
						log(f"VALUES:picked={column}, string={string}")
				elif event == 'SQL Search':
					if values['-table_music-'] == True:
						table = 'music'
					elif values['-table_movies-'] == True:
						table = 'movies'
					elif values['-table_series-'] == True:
						table = 'series'
					query_string = values['-DBMGR_QUERY_STRING-']
					if values['-QUERY_ACTIVE-'] == True:
						is_active = 1
					else:
						is_active = 0
					if query_string is not None:
						columns = np.get_columns(table)
						j = ','
						columns = str(j.join(columns))
						if is_active == 1:
							query_string = (query_string + " and isactive = '" + str(is_active) + "'")
						rows = np.querydb(table=table, column=columns, query=query_string)
						if rows is not None:
							UI.WINDOW['-PLAYLIST_ITEMS-'].update(rows)
						else:
							UI.WINDOW['-PLAYLIST_ITEMS-'].update("Looks like you better figure out how to search without that active flag....")
				elif event == 'Search':
					season = None
					table = UI.WINDOW['-PLAY_TYPE-'].Get()
					query_string = values['-SEARCH_QUERY-']
					is_active = MP.is_active
					if query_string is not None:
						if table is None:
							table = MP.conf['play_type']
						if table == 'series':
							if ':' in query_string:
								series_name = query_string.split(':')[0]
								season = query_string.split(':')[1]
								try:
									episode_number = query_string.split(':')[2]
									query_string = ("series_name like '%" + series_name + "%' and season = " + str(season) + " and episode_number = " + str(episode_number) + " and isactive = " + str(is_active))
								except:
									query_string = ("series_name like '%" + series_name + "%' and season = " + str(season) + " and isactive = " + str(is_active))
							else:
								series_name = query_string
								query_string = ("series_name like '%" + series_name + "%' and isactive = " + str(is_active))
								if season is not None:
									try:
										episode_number = query_string.split(':')[3]
										query_string = ("series_name like '%" + series_name + "%' and season = " + season + " episode_number = " + episode_number + " and isactive = '" + str(is_active) + "'")
									except:
										query_string = ("series_name like '%" + series_name + "%' and season = " + season + " and isactive = '" + str(is_active) + "'")
								log(f"Query string:{query_string}", 'info')
							rows = np.querydb(table='series', column='id,series_name,tmdbid,season,episode_number,episode_name,description,air_date,still_path,filepath', query=query_string)
							MP.playlist = np.create_media(rows=rows)
							if rows is not None:
								UI.WINDOW['-CURRENT_PLAYLIST-'].update(sorted(MP.playlist))
								MP.play_mode = 'playlist'
								UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
							else:
								UI.WINDOW['-CURRENT_PLAYLIST-'].update("Looks like you better figure out how to search without that active flag....")
						elif table == 'movies':
							query_string = ("title like '%" + query + "%' and isactive = '" + str(is_active) + "'")
							rows = querydb(table='movies', column='id,tmdbid,title,year,release_date,description,poster,filepath', query=query_string)
							MP.media = np.create_media(rows=rows)
							if rows is not None:
								UI.WINDOW['-CURRENT_PLAYLIST-'].update(sorted(MP.playlist))
								MP.play_mode = 'playlist'
								UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
						elif table == 'music':
							log(f"TODO: querydb music", 'info')
				elif event == '-PLAYLIST_ITEMS-':
					if values['-table_series-'] == True:
						table = 'series'
					elif values['-table_music-'] == True:
						table = 'music'
					elif values['-table_movies-'] == True:
						table = 'movies'
					try:
						_list = values['-PLAYLIST_ITEMS-'][0]
						_id = int(_list[0])
						sql_query = (f"select * from {table} where id = {_id};")
						results = sqlite3(sql_query)[0].split('|')
					except:
						results = ['null', 'null', 'null', 'null', 'null', 'null', 'null', 'null', 'null', 'null', 'null', 'null', 'null', 'null']
					columns = list(np.get_columns(table).keys())
					pos = -1
					for column in columns:
						pos += 1
						item = results[pos]
						key = (f"-{column}-")
						UI.WINDOW[key].update(item)
					UI.window.refresh()
				elif event == '-Update Info-':
					if values['-table_series-'] == True:
						table = 'series'
					elif values['-table_music-'] == True:
						table = 'music'
					elif values['-table_movies-'] == True:
						table = 'movies'
					schema = (np.get_columns(table))
					columns = list(schema.keys())
					for column in columns:
						_id = values['-id-']
						if column != 'id':
							dtype = schema[column]['data_type']
							is_required = schema[column]['is_required']
							key = (f"-{column}-")
							val = values[key]
							string = None
							if "'" in val:
								chunks = val.split("'")
								j = ''
								val = j.join(chunks)
							if '"' in val:
								chunks = val.split('"')
								j = ''
								val = j.join(chunks)
							if dtype == 'INTEGER' or dtype == 'BOOL':
								val = int(val)
								string = (f"{column} = {val}")
							elif dtype == 'TEXT':
								string = (f"{column} = '{val}'")
							sql_query = (f"update {table} set {string} where id = {_id};")
							ret = sqlite3(sql_query)[0]
							if ret:
								log(f"Error updating database: {ret}", 'error')
				elif event == 'Volume Up':
					MP.volume_up()
					log(f"ACTION:Volume up,{MP.conf['volume']}", 'info')
				elif event == 'Volume Down':
					MP.volume_down()
					log(f"ACTION:Volume down,{MP.conf['volume']}", 'info')
				elif event == '-Remove Selected-':
					for line in MP.dbmgr_picked_items:
						table = line.split(':')[0]
						series_name = line.split(':')[1]
						season = line.split(':')[2]
						episode_number = line.split(':')[3]
						episode_name = line.split(':')[4]
						_id = line.split(':')[5]
						query_string = ("id = " + str(_id))
						ret = np.removefromdb(table, query_string)
						MP.playlist.remove(line)
					MP.dbmgr_picked_items = []
					UI.window['-DBMGR_SELECTED_ROWS-'].update(MP.dbmgr_picked_items)
					log(f"Remove selected:{MP.dbmgr_picked_items}", 'info')
					UI.window['-PLAYLIST_ITEMS-'].update(sorted(MP.playlist))
				elif event == 'Torrent Manager':
					pbdl_win = start_pbdl('mgr')
					log(f"Loaded torrent manager!", 'info')
				elif event == 'Pirate Bay Downloader':
					pbdl_win = start_pbdl('dl')
					log(f"Loaded pirate bay downloader!", 'info')
				elif event == '-PBDL_SEARCH-':
					pbdl.results = pbdl.get_magnet(pbdl.pbdl_query, pbdl.category)
					UI.pbdl_dl_win['-PBDL_RESULTS-'].update(pbdl.results)
				elif event == '-PBDL_RESULTS-':
					key = values[event]
					if type(pbdl.results) == list:
						for item in pbdl.results:
							magnet = item[key]
							com = ("transmission-remote -a '" + magnet + "'")
				elif event == '-PBDL_SEARCH_QUERY-':
					pbdl.pbdl_query = values[event]
				elif event == 'youtube-dl':
					Y = np.ytdl()
					Y.start()
				elif event == 'Recenter UI':
					recenter_ui()
					log("EVENT:UI Recentered", 'info')
				elif event == "-Load Playlist-":
					path = file_browse_window()
					try:
						load_playlist(path)
					except Exception as e:
						log(f"No input provided! {e}", 'error')
				elif event == "-Save Playlist-":
					filepath = file_browse_window()
					if filepath is not None:
						try:
							ret = MP.save_playlist(filepath, MP.playlist)
							if ret is True:
								log(f"Save playlist: Success: {filepath}", 'info')
							else:
								log(f"Save playlist: Failed! {filepath}", 'info')
						except:
							log(f"No input provided! {e}", 'error')
				elif event == "-Load Directory-":
					MP.stop()
					path = folder_browse_window()
					if path is not None:
						try:
							MP.playlist = sorted(MP.load_directory(path))
							if MP.playlist is not None:
								UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.playlist)
								MP.play_mode = 'playlist'
								UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
								filepath = MP.playlist[0]
								MP.play(filepath)
						except Exception as e:
							log(f"Error: No user input provided: {e}", 'error')
					else:	
						np.log(f"Failed to load directory '{path}'.", 'error')
						MP.play_needed = 1
				elif event == "-Database Editor-":
					UI.db_editor()
				elif event == '-ID3 Tag Editor-':
					UI.tag_editor()
				elif event == '-PLAY_MODE-':
					MP.play_mode = values[event]
					log(f"Play mode changed:{MP.play_mode}", 'info')
					if MP.play_mode == 'database':
						MP.media = np.create_media()
						UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.PLAYLIST_ITEMS)
						MP.skip_next()
				elif event == '-Set Active-':
					log(f"TODO: Set active:{MP.dbmgr_picked_items}", 'info')
				elif event == '-Set Inactive-':
					log(f"TODO: Set inactive:{MP.dbmgr_picked_items}", 'info')
				elif event == '-Select All-':
					dbmgr_select_all()
				elif event == '-Clear All-':
					dbmgr_clear_all()
				elif event == '-VID_OUT-':
					log(f"Don't touch me, booger blaster!", 'info')
				elif event == 'Fix Focus':
					UI.WINDOW.TKroot.focus_force()
					UI.WINDOW.Element('-SEARCH_QUERY-').SetFocus()
					log(f"Set focus on search query input!", 'info')
				elif event == 'Fix Scaling':
					calculated_scale = np.calculate_scale(MP.conf['nowplaying']['filepath'])
					current_scale = P.video_get_scale()
					log(f"EVENT: Fix Scaling button: Previous:{current_scale}, New:{calculated_scale}", 'info')
					P.video_set_scale(calculated_scale)
				elif event == 'Screenshot':
					ret = MP.screenshot()
					np.log(ret, 'info')
				elif event in VLC_VIDEO_FILTERS or event in VLC_AUDIO_FILTERS:
					f = event
					log(f"Changing filter:{f}", 'info')
					ret = change_filter(f)
					np.log(ret, 'info')
				elif event == sg.WIN_CLOSED and MP.continuous == 0 and MP.conf['GUI_RESET'] == False:
					log(f"Window closed (gui): continuout=0, reset=False", 'info')
					np.writeConf(MP.conf)
					MP.exit = True
				elif event == '-Scan Music-':
					np.log(f"Scanning music dir: {MP.conf['media_directories']['music']}")
					np.scan_music()
					gui_reset()
				elif event == '-Scan Movies-':
					np.log(f"Scanning movies dir: {MP.conf['media_directories']['movies']}")
					np.scan_movies()
					gui_reset()
				elif event == '-Scan Series-':
					np.log(f"Scanning series dir: {MP.conf['media_directories']['series']}")
					np.scan_series()
					gui_reset()
				elif event == '-Scan All-':
					np.log(f"Scanning all media types: {MP.conf['media_directories']['main']}")
					np.scan_music()
					np.scan_movies()
					np.scan_series()
					gui_reset()
				elif event == 'Mark Intro: Start':
					MP.intro_start = P.get_time() * 1000
					np.log(f"Intro start marked: {MP.intro_start}", 'info')
				elif event == 'Mark Intro: End':
					MP.intro_end = P.get_time() / 1000
					duration = P.get_length() / 1000
					if MP.intro_start is None:
						MP.intro_start = 0.0
					np.log(f"Intro marked: start={MP.intro_start}, end={MP.intro_end}, duration={duration}", 'info')

					com = (f"python3 \"{np.HOME}/.local/lib/python3.8/site-packages/np/utils/insert_intro.py\" \"{MP.conf['nowplaying']['filepath']}\" {MP.intro_start} {MP.intro_end}&")
					subprocess.call(com, shell=True)
					np.log("TODO: Finish np.insert_intro(filepath, start, end)")
				else:
					if event is not None:
						try:
							log(f"np_main.py, function=uievents_handler(), Unhandled event and value received:{event}, {values[event]}", 'info')
						except Exception as e:
							log(f"np_main.py, function=uievents_handler(), Unhandled event received:{event}", 'info')

			if MP.conf['GUI_RESET'] == True:
				log(f"reset executing: {MP.conf['play_type']}", 'info')
				MP.conf = np.readConf()
				MP = np.nplayer()
				P = MP.init_vlc()
				media = np.create_media()
				MP.series_history = np.read_history()
				UI = np.gui()
				log("np_main.py: Created GUI from main loop ('GUI_RESET' = {MP.conf['GUI_RESET']}", 'info')
				set_video_out()
				MP.continuous = 1
				UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.playlist)
				UI.WINDOW['-PLAY_TYPE-'].update(MP.conf['play_type'])
				log("np_main.py: Resuming from reset = True...", 'info')
				MP.play()
				time.sleep(0.5)
				P.set_position(MP.conf['nowplaying']['play_pos'])
				log(f"np_main.start():RESUME:Skipped to {MP.conf['nowplaying']['play_pos']}", 'info')
				MP.continuous = 1
				MP.conf['GUI_RESET'] = False
				log(f"np_main.py:Reset finished (Reset set to false)! Conf written.", 'info')
				np.writeConf(MP.conf)
				recenter_ui()
			elif MP.play_needed == 1:
				log("Playing from 'play needed'", 'info')
				filepath = MP.conf['nowplaying']['filepath']
				play_pos = MP.conf['nowplaying']['play_pos']
				if filepath is not None:
					filepath = urllib.parse.unquote(filepath)
					log(f"using resume from file:{filepath}", 'info')
					MP.play(filepath)
					P.set_position(play_pos)
					log(f"np_main.start():play_needed=1:Skipped to {play_pos}", 'info')
				else:
					log ("Not resuming, filepath is None", 'info')
					if MP.play_mode == 'playlist':
						MP.next = MP.get_playlist_next()
						MP.play(MP.next)
					else:
						MP.play()
				MP.play_needed = 0	
			#if com or event handler set nplayer's 'exit' class attribute to True for any reason, stop main loop.
			if MP.exit == True:
				log(f"Exit (break)!", 'info')
				break
			#If nplayer's art update class attribute is set, update art.
			if MP.ART_UPDATE_NEEDED == True and P.is_playing():
				UI.WINDOW2['-VID_OUT-'].update(MP.album_art)
				log(f"art updated:{MP.album_art}", 'info')
				UI.WINDOW2.refresh()
				MP.ART_UPDATE_NEEDED = False
			# update elapsed time if there is a video loaded and the media is playing
			if P.is_playing() and MP.is_url == False:
				if MP.scale_needed == 1:
					calculated_scale = np.calculate_scale(MP.conf['nowplaying']['filepath'])
					current_scale = P.video_get_scale()
					P.video_set_scale(calculated_scale)
					log(f"Set scale by scale_needed flag: Previous:{current_scale}, New:{calculated_scale}", 'info')
					MP.scale_needed = 0
				if update >= update_ct:
					update = 0
					s='%20'
					j = ' '
					s2 = 'file://'
					MP.isplaying = True
					filepath = P.get_media().get_mrl().split("file://")[1]
					MP.conf['nowplaying']['filepath'] = urllib.parse.unquote(filepath)
					MP.conf['nowplaying']['play_pos'] = P.get_position()
					pos = (MP.conf['nowplaying']['play_pos'])
					old_pos = pos
					if MP.conf['intro']['start'] is not None and MP.conf['intro']['end'] is not None:
						if pos < MP.conf['intro']['end'] and pos > MP.conf['intro']['start']:
							start = MP.conf['intro']['start'] / 100
							end = MP.conf['intro']['end'] / 100
							if old_pos <= end:
								pos = (MP.conf['intro']['end'] + 0.05) / 100
								P.set_position(pos)
								np.log(f"Skipped intro: old={old_pos}, start={start}, end={end}", 'info')
								MP.conf['nowplaying']['play_pos'] = pos
								MP.conf['intro']['start'] = None
								MP.conf['intro']['end'] = None
							else:
								np.log("Position passed intro point: Current={old}, intro_end={end}", 'info')
								MP.conf['intro']['start'] = None
								MP.conf['intro']['end'] = None
					UI.WINDOW['-PLAY_POS-'].update(MP.conf['nowplaying']['play_pos'])
					txt = "{:02d}:{:02d} / {:02d}:{:02d}".format(*divmod(P.get_time()//1000, 60), *divmod(P.get_length()//1000, 60))
					if MP.next is not None:
						txt = (txt + "::" + str(MP.next))
					UI.WINDOW['-MESSAGE_AREA-'].update(txt)
			# if media is playing but it's a url, skip info update
			elif P.is_playing() and MP.is_url == True:
				pass
			# if media not playing, update status message
			else:
				MP.isplaying = False
				UI.WINDOW['-MESSAGE_AREA-'].update('Load media to start')
			stop_timer = timeit.default_timer()
			loop_time = stop_timer - start_timer
			ts = str(loop_time).split('.')[0]
		if readct > readmax:
			refresh_log_data()
			readct = 0
	UI.WINDOW.close()

def getpid():
	pid = None
	com = "pgrep -af np | grep -v \"/bin/sh\""
	lines = shell(com).split("\n")
	ret = []
	for line in lines:
		if 'np' in line:
			pid=line.split(" ")[0]
			ret.append(pid)
	return ret 

def ck_start():
	pids = getpid()
	if len(pids) < 2:
		isrunning = False
	else:
		isrunning = True
	if isrunning:
		import websocket
		c = websocket.create_connection('ws://192.168.2.2:8000/')
		c.send('create_gui')
		c.close()
	else:
		print ("starting")
		t = Thread(target = start)
		t.start()	

if __name__ == "__main__":
	ck_start()

