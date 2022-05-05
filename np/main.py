#!/usr/bin/env python3

import pafy
import urllib.parse
import PySimpleGUI as sg
import os
import subprocess
import np

querydb = np.querydb
input_handler = np.dev.input_handler
xrandr = np.xrandr
import pickle
import vlc
import random
import time


def ui_center():
	global UI
	UI.WINDOW.move(0, 0)
	UI.WINDOW2.move(0, 0)


def recenter_ui():
	screen = MP.conf['screen']
	try:
		state = 'visible'
		MP.conf['windows']['gui']['visible_status'] = state
		gui_x = int(MP.conf['windows']['gui'][state][screen]['x'])
		gui_y = int(MP.conf['windows']['gui'][state][screen]['y'])
		UI.WINDOW.move(gui_x, gui_y)
		UI.WINDOW2.move(int(MP.conf['windows']['viewer'][screen]['x']), int(MP.conf['windows']['viewer'][screen]['y']))
	except:
		MP.conf['windows'] = np.init_window_position()
		MP.conf['windows']['gui']['visible_status'] = state
		gui_x = int(MP.conf['windows']['gui'][state][screen]['x'])
		gui_y = int(MP.conf['windows']['gui'][state][screen]['y'])
		UI.WINDOW.move(gui_x, gui_y)
		screen = int(MP.conf['screen'])
		UI.WINDOW2.move(int(MP.conf['windows']['viewer'][screen]['x']), int(MP.conf['windows']['viewer'][screen]['y']))

def dbmgr_add_items(items=None):
	if items == None:
		items = UI.window['-DBMGR_SELECTED_ROWS-']
	all_items = UI.uivalues['-DBMGR_RESULTS-']
	for add in items:
		if add not in items:
			MP.dbmgr_picked_items.append(add)
	MP.dbmgr_picked_items = items
	UI.WINDOW['-DBMGR_SELECTED_ROWS-'].update(MP.dbmgr_picked_items)
	return MP.dbmgr_picked_items


def dbmgr_remove_items(items=None):
	if items == None:
		items = UI.window['-DBMGR_SELECTED_ROWS-']
	all_items = UI.uivalues['-DBMGR_RESULTS-']
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
	MP.dbmgr_picked_items = MP.media['DBMGR_RESULTS']
	UI.WINDOW['-DBMGR_SELECTED_ROWS-'].update(MP.dbmgr_picked_items)
			
def hide_ui(conf=None):
	if conf == None:
		MP.conf = np.readConf()
	screen = MP.conf['screen']
	try:
		state = 'hidden'
		MP.conf['windows']['gui']['visible_status'] = state
		x = int(MP.conf['windows']['gui'][state][screen]['x'])
		y = int(MP.conf['windows']['gui'][state][screen]['y'])
		UI.WINDOW.move(x, y)
	except Exception as e:
		print ('np_main_test, hide_ui, line 76', e)
		MP.conf['windows'] = np.init_window_position()
		state = 'hidden'
		MP.conf['windows']['gui']['visible_status'] = state
		x = int(MP.conf['windows']['gui'][state][screen]['x'])
		y = int(MP.conf['windows']['gui'][state][screen]['y'])
		UI.WINDOW.move(x, y)


def store_window_location():
	screen = MP.conf['screen']
	state = MP.conf['windows']['gui']['visible_status']
	MP.conf['windows']['gui'][state][screen]['x'], MP.conf['windows']['gui'][state][screen]['y'] = UI.WINDOW.current_location()
	np.writeConf(MP.conf)
	print ("Window location stored:", MP.conf['windows']['gui'][state][screen]['x'], MP.conf['windows']['gui'][state][screen]['y'])

def gui_reset(table, tab):
	global P, MP, UI
	MP.conf['play_type'] = table
	#np.writeConf(MP.conf)
	UI.RESET = True
	#print ("UI.RESET:", UI.RESET, " Table=", table)
	update_resume()
	#if play_file is not None:
	#	data = (UI.RESET, table, tab, play_pos, play_file)
	#else:
	#	data = (UI.RESET, table, tab, None, None)
	#with open ('nplayer.reset', 'wb') as f:
	#	pickle.dump(data, f)
	#f.close()
	MP.stop()
	UI.WINDOW.close()
	UI.WINDOW2.close()

def set_video_out():
	global MP, UI, P
	if MP.conf['video_player'] == 'vlc':
		#io = np.dev.input_handler()
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
		print (txt)
		return False
	if a == 'add':
		try:
			MP.conf = np.readConf()
			current_opts = MP.conf['vlc']['opts']
			opts = (current_opts + " " + f_string)
			MP.conf['vlc']['opts'] = opts
			#np.writeConf(MP.conf)
			print ("Updated audio filter options:", opts)
		except Exception as e:
			print ("Failed to set audio filter option:", e, f, MP.conf['vlc']['opts'])
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
			#np.writeConf(MP.conf)
			print ("Updated video filter options:", MP.conf['vlc']['opts'])
		except Exception as e:
			print ("Failed to remove video filter option:", e, f, MP.conf['vlc']['opts'])
			return False
	else:
		txt = ("Unknown action:" + a + ", Available: 'add', 'remove'")
		print (txt)
		return False
	gui_reset(MP.conf['play_type'], '-player_control_layout-')


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
	gui_reset(MP.conf['play_type'], '-player_control_layout-')


def update_resume():
	s='%20'
	j = ' '
	s2 = 'file://'
	filepath = P.get_media().get_mrl().split("file://")[1]
	MP.conf['nowplaying']['filepath'] = urllib.parse.unquote(filepath)
	MP.conf['nowplaying']['play_pos'] = P.get_position()
	#print ('set play pos:', MP.conf['nowplaying']['play_pos'])
	#print ('set nowplaying filepath:', MP.conf['nowplaying']['filepath'])
	np.writeConf(MP.conf)



def playlist_click(_id, table):
	query_string = ("id = " + str(_id))
	_file = np.querydb(table, 'filepath', query_string)[0][0]
	MP.play(_file)


def update_media_info(row):
	row = MP.dbmgr_picked_items
	row = row.split(':')
	#print (row)
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
			#print ("key, val:", key, val)
			UI.WINDOW[key].update(val)


def load_playlist(filepath):
	filepath = np.file_browse_window()
	MP.stop()
	if ".txt" in filepath:
		MP.media['DBMGR_RESULTS'] = MP.load_playlist(filepath)
		UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.media['DBMGR_RESULTS'])
		MP.play_mode = 'playlist'
		UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
		filepath = MP.media['DBMGR_RESULTS'][0]
		MP.play(filepath)
	else:
		MP.play_mode = 'database'
		UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
		MP.play(filepath)


def start():
	global P, MP, UI, conf
	conf = None
	btn = None
	subprocess.check_output('sudo chmod -R a+rwx /dev/input/', shell=True)
	MP = np.nplayer()
	P = MP.init_vlc()
	media = np.create_media()
	tab = '-player_control_layout-'
	MP.conf = np.readConf()
	#print ("Loaded play type:", MP.conf['play_type'])
	if MP.conf is None:
		print ("conf is None, re-initializing...")
		MP.conf = np.initConf()
		print ("Defaults restored.")
		MP.conf['screens'] = xrandr()
	screen = MP.conf['screen']
	MP.conf['w'] = MP.conf['screens'][screen]['w']
	MP.conf['h'] = MP.conf['screens'][screen]['h']
	MP.conf['pos_x'] = MP.conf['screens'][screen]['pos_x']
	MP.conf['pos_y'] = MP.conf['screens'][screen]['pos_y']
	try:
		media['series_history'] = np.read_history()
	except Exception as e:
		print ("Series history is empty or couldn't read pickle data: line 557,", e)
		media['series_history'] = {}
	UI = np.gui()
	try:
		init = MP.conf['init']
	except:
		MP.conf['init'] = True
		MP.conf['windows'] = np.init_window_position()
		MP.conf['windows']['gui']['visible_status'] = 'visible'
		np.writeConf(MP.conf)
		ui_center()
	pbdl = np.pbdl()
	set_video_out()
	media['continuous'] = 1
	input_enabled = 0
	btn = None
	while True:
		try:
			com = None
			with open (np.COMFILE, 'r') as f:
				data = f.read().strip()
				f.close()
			with open (np.COMFILE, 'w') as f:
				f.write('')
				f.close()
		except:
			with open (np.COMFILE, 'w') as f:
				data = ''
				f.write(data)
				f.close()
				data = None
		if data is not None and data != '':
			com = data.split('=')[0]
			try:
				arg = data.split('=')[1]
			except:
				arg = None
			if com == 'play':					
				MP.play()
				np.log("REMOTE: Playing!", 'info')
			elif com == 'pause':
				P.pause()
				np.log("REMOTE: Paused")
			elif com == 'stop':
				MP.stop()
				np.log("REMOTE: Stopped", 'info')
			elif com == 'skip_next':
				MP.skip_next()
				np.log("REMOTE: Skipped Next", 'info')
			elif com == 'skip_prev':
				MP.skip_previous()
				np.log("REMOTE: Skipped Previous")
			elif com == 'vol_set':
				MP.volume_set(arg)
				np.log("REMOTE: vol_set", 'info')
			elif com == 'vol_up':
				np.log("REMOTE: volume_up", 'info')
				MP.volume_up()
			elif com == 'vol_down':
				MP.volume_down()
				np.log("REMOTE: volume_down", 'info')
			elif com == 'mute':
				MP.volume_set(0)
				np.log("REMOTE: Mute")
			elif com == 'unmute':
				vol = int(self.conf['volume'])
				MP.volume_set(vol)
				np.log("REMOTE: Unmuted", 'info')
			elif com == 'quit':
				np.log("REMOTE: Quitting...", 'info')
				UI.WINDOW.close()
				UI.WINDOW2.close()
				break
			elif com == 'load':
				txt = ("REMOTE: Loading file:" + str(arg))
				np.log(txt, 'info')
				load_playlist(arg)
			elif com == 'play_mode':
				MP.play_mode = arg
				txt = ("REMOTE: Play mode set:" + str(arg))
				np.log(txt, 'info')
			elif com == 'play_type':
				MP.play_type = arg
				txt = ("REMOTE: Play type set:" + str(arg))
				np.log(txt, 'info')
		UI.window, UI.uievent, UI.uivalues = UI.get_events()
		if UI.uievent is None and UI.uivalues is None:
			pass
		
		if btn is not None:
			if btn == MP.KEY_EVENTS['SEEK_FWD']:
				seek_fwd()
			elif btn == MP.KEY_EVENTS['SEEK_REV']:
				seek_rev()
			elif btn == MP.KEY_EVENTS['SCALE_UP']:
				scale = P.video_get_scale()
				scale = float(scale + 0.1)
				P.video_set_scale(scale)
			elif btn == MP.KEY_EVENTS['SCALE_DOWN']:
				scale = P.video_get_scale()
				scale = float(scale - 0.1)
				P.video_set_scale(scale)
			elif btn == MP.KEY_EVENTS['FULLSCREEN']:
				P.toggle_fullscreen()
				MP.conf['fullscreen'] = P.get_fullscreen()
			elif btn == MP.KEY_EVENTS['PAUSE']:
				P.pause()
			elif btn == MP.KEY_EVENTS['SKIP_NEXT']:
				MP.skip_next()
			elif btn == MP.KEY_EVENTS['SKIP_PREV']:
				MP.skip_previous()
			btn = None				
#-----------UI Events section start------------------#
		if UI.uievent == sg.WIN_CLOSED and UI.RESET == True:
			#print ("reset executing...", MP.conf['play_type'])
			MP = np.nplayer()
			P = MP.init_vlc()
			media = np.create_media()
			media['series_history'] = np.read_history()
			UI = np.gui()
			set_video_out()
			media['continuous'] = 1
			UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.DBMGR_RESULTS)
			if tab == '-db_mgr_layout-':
				UI.WINDOW['-db_mgr_layout-'].select()
			if tab == '-player_control_layout-':
				UI.WINDOW['-player_control_layout-'].select()
			if tab == '-pbdl_layout-':
				UI.WINDOW['-pbdl_layout-'].select()
			#if MP.conf['play_type'] == 'series':
			UI.WINDOW['-PLAY_TYPE-'].update(MP.conf['play_type'])
			#	UI.WINDOW['-table_movies-'].update(False)
			#	UI.WINDOW['-table_music-'].update(False)
			#if MP.conf['play_type'] == 'movies':
			#	UI.WINDOW['-table_series-'].update(False)
			#	UI.WINDOW['-table_movies-'].update(True)
			#	UI.WINDOW['-table_music-'].update(False)
			#if MP.conf['play_type'] == 'music':
			#	UI.WINDOW['-table_series-'].update(False)
			#	UI.WINDOW['-table_movies-'].update(False)
			#	UI.WINDOW['-table_music-'].update(True)
			#if MP.conf['nowplaying']['filepath'] is not None:
			#print ("Resuming from reset = True...")
			#MP.play(MP.conf['nowplaying']['filepath'])
			MP.play()
			time.sleep(0.5)
			P.set_position(MP.conf['nowplaying']['play_pos'])
			#print ("Skipped to ", play_pos)
			media['continuous'] = 1
			#MP.conf['nowplaying']['filepath'] = None
			np.writeConf(MP.conf)
			UI.RESET = False
			#MP.play_needed = 0
			#print ("Reset flag unset:", UI.RESET)
		if MP.play_needed == 1:
			#print ("Playing from 'play needed'")
			filepath = MP.conf['nowplaying']['filepath']
			play_pos = MP.conf['nowplaying']['play_pos']
			if filepath is not None:
				filepath = urllib.parse.unquote(filepath)
				#print ('using resume from file:', filepath)
				MP.play(filepath)
				P.set_position(play_pos)
			else:
				print ('not resuming...', filepath)
				if MP.play_mode == 'playlist':
					MP.next = MP.get_playlist_next()
					MP.play(MP.next)
				else:
					MP.play()

			play_needed = 0	
		if UI.uievent == sg.WIN_CLOSED and media['continuous'] == 0 and UI.RESET == False:
			#print ("Breaking: continuous = 0")
			#now playing file ('next') and position
			np.writeConf(MP.conf)
			break
		if UI.uievent == 'Toggle Network':
			mode = MP.toggle_network_mode()
			print ("Network mode changed:", mode)
		if UI.uievent == 'Hide UI':
			hide_ui()
		if UI.uievent == 'store window location':
			store_window_location()
		if UI.uievent == 'Exit' or UI.uievent == 'Close':
			update_resume()
			break
		#if UI.uievent == 'store_window location':
		#	gui_location = UI.WINDOW.current_location()
		#	print ("GUI Window Location:", gui_location)
		if UI.uievent == '-episode_number-' or UI.uievent == '-filepath-' or UI.uievent == '-series_name-' or UI.uievent == '-season-':
			k = UI.uievent
			v = UI.uivalues[UI.uievent]
			MP.target[k] = v
			#print ("set target(", k, ") to ", v)
		if UI.uievent == '-Query TMDB-':
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
					
		if UI.uievent == '-table_series-' or UI.uievent == '-table_movies-' or UI.uievent == '-table_music-' or UI.uievent == '-PLAY_TYPE-':
			if UI.uievent == '-PLAY_TYPE-':
				play_type = UI.uivalues[UI.uievent]
				#print ("Play type changed:", play_type)
				gui_reset(play_type, '-player_control_layout-')
				#np.writeConf(MP.conf)
			if UI.uievent == '-table_series-':
				gui_reset('series', '-db_mgr_layout-')
			elif UI.uievent == '-table_movies-':
				gui_reset('movies', '-db_mgr_layout-')
			elif UI.uievent == '-table_music-':
				gui_reset('music', '-db_mgr_layout-')
		elif UI.uievent == '-pbdl_table_series-' or UI.uievent == '-pbdl_table_movies-' or UI.uievent == '-pbdl_table_music-':
			#print ("Table changed...", UI.uivalues[UI.uievent])
			if UI.uievent == '-pbdl_table_series-':
				gui_reset('series', '-db_mgr_layout-')
			elif UI.uievent == '-pbdl_table_movies-':
				gui_reset('movies', '-db_mgr_layout-')
			elif UI.uievent == '-pbdl_table_music-':
				gui_reset('music', '-db_mgr_layout-')
			
		elif UI.uievent == '-setactive-':
			val = UI.uivalues[UI.uievent]
			if val == False:
				isactive=0
			elif val == True:
				isactive=1
			else:
				isactive=1
		elif UI.uievent == '-PLAY_POS-':
			val = float(UI.uivalues[UI.uievent])
			P.set_position(val)
		elif UI.uievent == 'play':
			P.play()
		elif UI.uievent == 'pause':
			P.pause()
		elif UI.uievent == 'stop':
			P.stop()
		elif UI.uievent == 'next':
			MP.skip_next()
		elif UI.uievent == 'previous':
			MP.skip_previous()
		elif UI.uievent == 'rotate 90':
			rotate(90)
		elif UI.uievent == 'seek fwd':
			MP.seek_fwd()
		elif UI.uievent == 'seek rev':
			MP.seek_rev()
		elif UI.uievent == 'fullscreen':
			if MP.conf['fullscreen'] == 1:
				fs = 0
			elif MP.conf['fullscreen'] == 0:
				fs = 1
			if fs == 1:
				P.set_fullscreen(True)
			elif fs == 0:
				P.set_fullscreen(False)
			np.updateConf(conf, 'fullscreen', fs)
		elif UI.uievent == '-SET_SCREEN-':
			MP.conf['screen'] = int(UI.uivalues[UI.uievent])
			np.writeConf(MP.conf)
			#print ("Active screen updated! Needs restart", MP.conf['screen'])
			gui_reset(MP.conf['play_type'], '-player_control_layout-')	
		elif UI.uievent == 'load':
			MP.stop()
			MP.next = UI.uivalues['-VIDEO_LOCATION-']
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
			else:
				MP.is_url = False
				MP.play(MP.next)
		elif UI.uievent == 'Refresh from Database':
			MP.media = np.create_media()
			UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.DBMGR_RESULTS)
			
		elif UI.uievent == 'VPN On/Off':
			if VPN == True:
				VPN = False
			elif VPN == False:
				VPN = True
			UI.toggle_vpn()
		elif UI.uievent == '-CURRENT_PLAYLIST-':
			MP.selected_playlist_item
			val = None
			_id = None
			table = None
			if MP.play_mode == 'playlist':
				val = UI.uivalues[UI.uievent][0]
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
						val = UI.uivalues[UI.uievent][0]
						_id = val.split(':')[6]
						table = val.split(':')[0]
						playlist_click(_id, table)
				else:
					MP.play(val)
			elif MP.play_mode == 'database':
				if MP.conf['play_type'] == 'series':
					try:
						val = UI.uivalues[UI.uievent][0]
						_id = val.split(':')[5]
						table = val.split(':')[0]
						playlist_click(_id, table)
					except Exception as e:
						print ("Error: Series list is empty! Details:", e, val, _id, table)
				elif MP.conf['play_type'] == 'movies':
					try:
						val = UI.uivalues[UI.uievent][0]
						table = val.split(':')[0]
						title = val.split(':')[1]
						year = val.split(':')[2]
						_id = val.split(':')[3]
						playlist_click(_id, table)
					except Exception as e:
						print ("Error: Movies list is empty! Details:", e, val, _id, table)
				elif MP.conf['play_type'] == 'music':
					try:
						val = UI.uivalues[UI.uievent][0]
						_id = val.split(':')[6]
						table = val.split(':')[0]
						playlist_click(_id, table)
					except Exception as e:
						print ("Error: List is empty! Details:", e, val, _id, table)
		elif UI.uievent == '-DBMGR_PICKED_COLUMNS-':
			string = None
			if len(UI.uivalues[UI.uievent]) == 1:
				column = str(UI.uivalues[UI.uievent][0])
				string = (column + " like '%%'")
				UI.WINDOW['-DBMGR_QUERY_STRING-'].update(string)
			else:
				for column in UI.uivalues[UI.uievent]:
					if string == None:
						string = (column + " like '%%'")
					else:
						string = (string + " and " + column + " = ''")
				UI.WINDOW['-DBMGR_QUERY_STRING-'].update(string)
			UI.WINDOW.refresh()
		elif UI.uievent == 'SQL Search':
			query_string = UI.uivalues['-DBMGR_QUERY_STRING-']
			ckbox = UI.isactive
			if ckbox:
				is_active = 1
			else:
				is_active = 0
			if query_string is not None:
				table = MP.conf['play_type']
				if table == 'series':
					query_string = (query_string + " and isactive = '" + str(is_active) + "'")
					rows = np.querydb(table='series', column='id,series_name,tmdbid,season,episode_number,episode_name,description,air_date,still_path,filepath', query=query_string)
					MP.media = np.create_media(rows=rows)
					if rows is not None:
						UI.WINDOW['-DBMGR_RESULTS-'].update(MP.media['DBMGR_RESULTS'])
						
					else:
						UI.WINDOW['-DBMGR_RESULTS-'].update("Looks like you better figure out how to search without that active flag....")
		elif UI.uievent == 'Search':
			season = None
			table = MP.conf['play_type']
			query_string = UI.uivalues['-SEARCH_QUERY-']
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

					print ("Query string:", query_string)
					rows = np.querydb(table='series', column='id,series_name,tmdbid,season,episode_number,episode_name,description,air_date,still_path,filepath', query=query_string)
					MP.media = np.create_media(rows=rows)
					if rows is not None:
						UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.media['DBMGR_RESULTS'])
						MP.play_mode = 'playlist'
						UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
					else:
						UI.WINDOW['-CURRENT_PLAYLIST-'].update("Looks like you better figure out how to search without that active flag....")
				elif table == 'movies':
					query_string = ("title like '%" + query + "%' and isactive = '" + str(is_active) + "'")
					rows = querydb(table='movies', column='id,tmdbid,title,year,release_date,description,poster,filepath', query=query_string)
					MP.media = np.create_media(rows=rows)
					if rows is not None:
						UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.media['DBMGR_RESULTS'])
						MP.play_mode = 'playlist'
						UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
				elif table == 'music':
					print ("TODO: querydb music")
					#rows = querydb(table = 'music', column='id,title,accoustic_id,album,album_id,artist_id,year,artist,track,track_ct,filepath', query='isactive = 1')


		elif UI.uievent == '-DBMGR_RESULTS-':
			MP.dbmgr_picked_items = UI.uivalues['-DBMGR_RESULTS-']
			UI.window['-DBMGR_SELECTED_ROWS-'].update(MP.dbmgr_picked_items)
			UI.window.refresh()
			#print (UI.uievent, UI.uivalues[UI.uievent])
			#except Exception as e:
			#	row = None
			#	print ("Exception:", e)
			# insert if radio button table == series, conditionals for others.
			#UI.update_series_info_from_row(row)
		elif UI.uievent == 'Volume Up':
			MP.volume_up()
			print ("Volume up:", MP.conf['volume'])
		elif UI.uievent == 'Volume Down':
			MP.volume_down()
			print ("Volume down:", MP.conf['volume'])
		elif UI.uievent == '-Remove Selected-':
			for line in MP.dbmgr_picked_items:
				table = line.split(':')[0]
				series_name = line.split(':')[1]
				season = line.split(':')[2]
				episode_number = line.split(':')[3]
				episode_name = line.split(':')[4]
				_id = line.split(':')[5]
				query_string = ("id = " + str(_id))
				ret = np.removefromdb(table, query_string)
				MP.media['DBMGR_RESULTS'].remove(line)
			MP.dbmgr_picked_items = []
			UI.window['-DBMGR_SELECTED_ROWS-'].update(MP.dbmgr_picked_items)
			#print ("Remove selected:", MP.dbmgr_picked_items)
			UI.window['-DBMGR_RESULTS-'].update(MP.media['DBMGR_RESULTS'])
		elif UI.uievent == 'Torrent Manager':
			pbdl.create_window()
			pbdl.get_torrents()
			pbdl.run()
		elif UI.uievent == 'Pirate Bay Downloader':
			if pbdl.downloader == False:
				UI.pbdl_dl_win = pbdl.create_downloader()
				print ("Loaded pirate bay downloader!")
			else:
				print ("Pirate bay downloader alread running!")
			pbdl.run()
		elif UI.uievent == '-PBDL_SEARCH-':
			pbdl.results = pbdl.get_magnet(pbdl.pbdl_query, pbdl.category)
			print (pbdl.results)
			UI.pbdl_dl_win['-PBDL_RESULTS-'].update(pbdl.results)
		elif UI.uievent == '-PBDL_RESULTS-':
			key = UI.uivalues[UI.uievent]
			if type(pbdl.results) == list:
				for item in pbdl.results:
					magnet = item[key]
					com = ("transmission-remote -a '" + magnet + "'")
					print (com)
		elif UI.uievent == '-PBDL_SEARCH_QUERY-':
			pbdl.pbdl_query = UI.uivalues[UI.uievent]
			print (pbdl.pbdl_query)
		elif UI.uievent == 'youtube-dl':
			Y = np.ytdl()
			Y.start()
		elif UI.uievent == 'Recenter UI':
			recenter_ui()
		elif UI.uievent == "-Load Playlist-":
			load_playlist(UI.uivalues[UI.uievent])
		elif UI.uievent == "-Save Playlist-":
			filepath = np.file_browse_window()
			ret = MP.save_playlist(filepath, MP.media['DBMGR_RESULTS'])
			if ret is True:
				print ("Success!")
			else:
				print ("Failed!")
		elif UI.uievent== "-Load Directory-":
			path = np.folder_browse_window()
			MP.stop()
			MP.media['DBMGR_RESULTS'] = MP.load_directory(path)
			UI.WINDOW['-CURRENT_PLAYLIST-'].update(MP.media['DBMGR_RESULTS'])
			MP.play_mode = 'playlist'
			UI.WINDOW['-PLAY_MODE-'].update(MP.play_mode)
			filepath = MP.media['DBMGR_RESULTS'][0]
			MP.play(filepath)
			#print (string)
		elif UI.uievent == '-PLAY_MODE-':
			MP.play_mode = UI.uivalues[UI.uievent]
			print ("Play mode changed:", MP.play_mode)
#		elif UI.uievent == '-Read Info-':
#			for item in MP.dbmgr_picked_items:
#				UI.update_series_info_from_row(item)
				#print ("Read current database info:", item)
#		elif UI.uievent == '-Update Info-':
#			for item in MP.dbmgr_picked_items:
#				print ("TODO: update database", item)
		elif UI.uievent == '-Set Active-':
			print ("TODO: Set active", MP.dbmgr_picked_items)
		elif UI.uievent == '-Set Inactive-':
			print ("TODO: Set inactive", MP.dbmgr_picked_items)
		elif UI.uievent == '-Select All-':
			dbmgr_select_all()
		elif UI.uievent == '-Clear All-':
			dbmgr_clear_all()
		elif UI.uievent == 'Hide UI':
			print ("GUI Menu hidden!")
		elif UI.uievent == '-VID_OUT-':
			print ("Don't touch me, booger blaster!")
		elif UI.uievent == 'Fix Focus':
			UI.WINDOW.TKroot.focus_force()
			UI.WINDOW.Element('-SEARCH_QUERY-').SetFocus()
			print ("Set focus on search query input!")
		elif UI.uievent == 'Screenshot':
			ret = MP.screenshot()
			print (ret)
		elif UI.uievent in np.VLC_VIDEO_FILTERS or UI.uievent in np.VLC_AUDIO_FILTERS:
			f = UI.uievent
			print ("Changing filter:", f)
			ret = change_filter(f)
			print (ret)
		else:
			if UI.uievent != '__TIMEOUT__' and UI.uievent is not None:
				try:
					print (UI.uievent, UI.uivalues[UI.uievent])
				except Exception as e:
					print ("np.py, function=start(), line 598, no value for event:", UI.uievent, UI.uivalues)
#-----------------UI Event section end------------------#

#-----------------
		if MP.ART_UPDATE_NEEDED == True and P.is_playing():
			UI.WINDOW2['-VID_OUT-'].update(MP.album_art)
			print ("art updated!", MP.album_art)
			UI.WINDOW2.refresh()
			MP.ART_UPDATE_NEEDED = False
	# update elapsed time if there is a video loaded and the media is playing
		if P.is_playing() and MP.is_url == False:
			s='%20'
			j = ' '
			s2 = 'file://'
			media['is_playing'] = 1
			filepath = P.get_media().get_mrl().split("file://")[1]
			MP.conf['nowplaying']['filepath'] = urllib.parse.unquote(filepath)
			MP.conf['nowplaying']['play_pos'] = P.get_position()
			pos = (MP.conf['nowplaying']['play_pos'])
			UI.WINDOW['-PLAY_POS-'].update(MP.conf['nowplaying']['play_pos'])
			txt = "{:02d}:{:02d} / {:02d}:{:02d}".format(*divmod(P.get_time()//1000, 60), *divmod(P.get_length()//1000, 60))
			if MP.next is not None:
				txt = (txt + "::" + str(MP.next))
			UI.WINDOW['-MESSAGE_AREA-'].update(txt)
		elif P.is_playing() and MP.is_url == True:
			pass

		else:
			media['is_playing'] = 0
			UI.WINDOW['-MESSAGE_AREA-'].update('Load media to start')

	UI.WINDOW.close()
	

if __name__ == "__main__":
	start()

