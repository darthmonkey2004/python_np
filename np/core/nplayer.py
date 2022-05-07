import subprocess
import pathlib
import os
import pafy
from PIL import Image, ImageTk
import requests
import subprocess
import eyed3
from urllib.parse import quote, unquote
import np
#input_handler = np.dev.input_handler
import vlc
import random
import time
import json

#-------------main player class=------------#
class nplayer():
	def __init__(self):
		self.loop = True
		self.is_url = False
		self.nowplaying = {}
		self.nowplaying['pos'] = None
		self.nowplaying['vw'] = None
		self.nowplaying['vh'] = None
		self.create_media = np.core.core.create_media
		self.conf = {}
		self.conf['vlc'] = {}
		self.conf['vlc']['opts'] = "--no-xlib"
		self.conf = np.readConf()
		if self.conf == None:
			self.conf = np.initConf()
			self.conf['windows'] = np.init_window_position()
		self.conf['grab_devices'] = ['/dev/input/event11']
		if self.conf['vlc']['opts'] is None:
			self.conf['vlc']['opts'] = "--no-xlib"
		self.media = {}
		self.media = np.create_media(self.conf['play_type'])
		self.history_pos = 0
		self.btn = None
		self.KEY_EVENTS = self.init_events()
		self.history = {}
		self.history['history'] = []
		self.history['pos'] = len(self.history['history']) - 1
		self.history['playing_from_history'] = False
		self.events_conf = 'events.conf'
		self.play_needed = 1
		self.scale_needed = 0
		self.DBMGR_RESULTS = self.media['DBMGR_RESULTS']
		self.dbmgr_picked_items = []
		self.target = {}
		self.target['file'] = None
		self.target['episode_number'] = None
		self.target['series_name'] = None
		self.target['season'] = None
		self.target['title'] = None
		self.next = None
		self.ART_UPDATE_NEEDED = False
		self.is_active = 1
		self.screencaps = np.CAPTURE_DIR
		self.is_recording = False
		self.vlcInstance = None
		self.selected_playlist_item = None
		self.play_mode = 'database'
		self.playlist = []
		self.playlist_last = None
		self.playlist_loop_one = False
		self.playlist_loop_all = True

		try:
			self.main_keyboard = self.conf['main_keyboard']['path']
		except:
			self.main_keyboard = None


	def toggle_network_mode(self):
		if self.conf['network_mode']['mode'] == 'local':
			self.conf['network_mode']['mode'] = 'remote'
		elif self.conf['network_mode']['mode'] == 'remote':
			self.conf['network_mode']['mode'] = 'local'
		np.writeConf(self.conf)
		return self.conf['network_mode']['mode']


	def init_events(self):
		if np.KEY_EVENTS == {}:
			self.KEY_EVENTS['SEEK_FWD'] = 208
			self.KEY_EVENTS['SEEK_REV'] = 168
			self.KEY_EVENTS['SCALE_UP'] = 165
			self.KEY_EVENTS['SCALE_DOWN'] = 163
			self.KEY_EVENTS['FULLSCREEN'] = 164
			self.KEY_EVENTS['PAUSE'] = 113
			self.KEY_EVENTS['SKIP_NEXT'] = 115
			self.KEY_EVENTS['SKIP_PREV'] = 114
		else:
			self.KEY_EVENTS = np.KEY_EVENTS
		return self.KEY_EVENTS




	def seek_to_pos(self, pos):
		self.pos = pos / 60
		try:
			self.player.set_position(self.pos)
			return self.pos
		except Exception as e:
			np.log("seek_to_pos, line 236" + str(e))
			return 1


	def playback_started(self):
		self.media['is_playing'] = 1
		self.play_needed = 0
	
	def playback_finished(self):
		np.log("Playback finished!")
		self.nowplaying['filepath'] = None
		self.play_needed = 1


	def init_vlc(self, uri=None):
		try:
			opts = self.conf['vlc']['opts']
		except:
			opts = "--no-xlib"
		self.vlcInstance = vlc.Instance(opts)
		if uri == None:
			self.player = self.vlcInstance.media_player_new()
		else:
			self.player = self.vlcInstance.media_player_new(uri)
		self.player.audio_set_mute(self.conf['mute'])
		if self.conf['mute'] == False:
			self.player.audio_set_volume(self.conf['volume'])
		scale = self.conf['scale']
		if scale >= 10:
			self.scale = float(scale / 100)#Convert to 1-10 float value if in percentage
		else:
			self.scale = float(scale)#force to float if already in 1-10 scale
		time.sleep(0.5)
		self.player.video_set_scale(scale)
		for evt in self.media['vlc']['events']:
			evid = int(evt.split(':')[0])
			event = vlc.EventType(evid)
			self.player.event_manager().event_attach(event, self.vlc_event)
		return self.player



	def set_now_playing(self):
		self.nowplaying['scale'] = self.player.video_get_scale()
		self.nowplaying['fps'] = self.player.get_fps()
		self.nowplaying['vw'] = self.player.video_get_width()
		self.nowplaying['vh'] = self.player.video_get_height()
		self.nowplaying['fullscreen'] = self.player.get_fullscreen()
		self.nowplaying['vlc_media_object'] = self.player.get_media()
		self.nowplaying['state'] = self.player.get_state()
		self.nowplaying['xwindow'] = self.player.get_xwindow()
		self.conf['nowplaying']['play_pos'] = self.player.get_position()
		return self.nowplaying
		
	def vlc_event(self, event):
		vlcdict = self.media['vlc']
		self.nowplaying = self.media['now_playing']
		typestr = (str(event.type) + ":")
		for event in vlcdict['events']:
			if typestr in event:
				event = event.split(':')[1]
				if event == 'EventType.MediaMPEndReached':
					self.play_needed = 1
					self.conf['nowplaying']['filepath'] = None
					np.writeConf(self.conf)
					self.playback_finished()
				elif event == 'EventType.MediaMPPaused':
					pass
				elif event == 'EventType.MediaMPTimeChanged':
					self.nowplaying['time'] = self.player.get_time()
					self.nowplaying['duration'] = self.player.get_length()
				elif event == 'EventType.MediaMPPositionChanged':
					self.conf['nowplaying']['play_pos'] = self.player.get_position()
					self.nowplaying['vw'] = self.player.video_get_width()
					self.nowplaying['vh'] = self.player.video_get_height()
					if self.conf['nowplaying']['play_pos'] == 1.0 or self.conf['nowplaying']['play_pos'] >= 0.999:
						np.log("Plaback nearly ending...")
						self.nowplaying['vw'] = None
						self.nowplaying['vh'] = None
					if self.conf['nowplaying']['play_pos'] or self.conf['nowplaying']['play_pos'] <= 0.001:
						self.playback_started()
				elif event == 'EventType.MediaMPMediaChanged':
					self.nowplaying = self.set_now_playing()
				elif event == 'EventType.MediaMPScrambledChanged':
					self.nowplaying['scrambled'] = self.player.program_scrambled()
				elif event == 'EventType.MediaMPSeekableChanged':
					self.nowplaying['is_seekable'] = self.player.is_seekable()
				elif event == 'EventType.MediaMPPausableChanged':
					pass
				elif event == 'EventType.MediaMPTitleChanged':
					self.nowplaying['title'] = self.player.get_title()
				elif event == 'EventType.MediaMPLengthChanged':
					self.nowplaying['duration'] = self.player.get_length()
				elif event == 'EventType.MediaMPPlaying':
					self.media['is_playing'] = self.player.is_playing()
					self.play_needed = 0
				elif event == 'EventType.MediaMPAudioDevice':
					self.audio_device = self.player.audio_output_device_get()
				elif event == 'EventType.MediaMPAudioVolume':
					self.nowplaying['volume'] = self.player.audio_get_volume()
				elif event == 'EventType.MediaMPStopped':
					self.nowplaying['is_playing'] = self.player.is_playing()
					self.media['is_playing'] = 0
				elif event == 'EventType.MediaMPEncounteredError':
					np.log("Uh, oh... spaghetti ohs.")
				elif event == 'EventType.MediaMPVout':
					pass
				elif event == 'EventType.MediaMPChapterChanged':
					self.chapter = self.player.get_chapter()
					np.log("Chapter changed:" + str(self.chapter))
				else:
					np.log("VLC Event callback running:" + str(event))


#------------playlist/dbmgr functions----------------#

	def get_info_string(self, filepath):
		strings = []
		qstring = ("filepath = '" + filepath + "'")
		item = np.querydb(table='series', column='series_name,season,episode_number,episode_name,id', query=qstring)
		try:
			series_name, season, episode_number, episode_name, _id = item[0]
			string = ("series:" + series_name + ":" + str(season) + ":" + str(episode_number) + ":" + episode_name + ":" + str(_id))
		except:
			string = ("Unknown: " + filepath)
		return string
			
	def get_next(self):
		#self.next = None
		if self.conf['play_type'] == 'series':
			np.log("get next: series started!")
			_list = np.querydb(table='series', column='distinct series_name', query='isactive = 1')
			l = len(_list) - 1
			pickno = random.randint(0, l)
			series_name = str(_list[pickno][0])
			qstring = ("series_name like '%" + series_name + "%'")
			items = np.querydb(table='series', column='filepath', query=qstring)
			_list=[]
			for item in items:
				_list.append(item[0])
			#try:
			self.series_history = np.read_history()
			try:
				self.last = self.series_history[series_name]
			except:
				self.last = None
			if self.last in _list and self.last is not None:
				np.log("Last in list:" + self.last)
				idx = int(_list.index(self.last))
				idx = idx + 1
				try:
					self.next = _list[idx]
					self.selected_playlist_item = self.get_info_string(self.next)
					np.log("Next set! Series Name, Index, Next:" + series_name + ", " + str(idx) + ", " + self.next)
				except:
					self.next = _list[0]
					self.selected_playlist_item = self.get_info_string(self.next)
					np.log("Next not set (reset to 0)! Series Name, Index, Next:" + series_name + ", " + str(idx) + ", " + self.next)
				if self.history['playing_from_history'] == False:
					self.history['history'].append(self.next)
				elif self.history['playing_from_history'] == True:
					self.skip_next()
				self.series_history[series_name] = self.next
				np.write_history(self.series_history)
			elif self.last is None:
				self.next = _list[0]
				self.series_history[series_name] = self.next
				np.write_history(self.series_history)
			else:
				txt = ("Last file recorded not in playlist:" + self.last + ", " + str(_list))
				np.log(txt, 'warning')
			return self.next
		elif self.conf['play_type'] == 'movies':
			_list = np.querydb(table='movies', column='filepath', query='isactive = 1')
			l = len(_list) - 1
			pickno = random.randint(0, l)
			self.next = str(_list[pickno][0])
			if self.history['playing_from_history'] == False:
				self.history['history'].append(self.next)
			return self.next
		elif self.conf['play_type'] == 'music':
			_list = np.querydb(table='music', column='filepath', query='isactive = 1')
			l = len(_list) - 1
			pickno = random.randint(0, l)
			self.next = str(_list[pickno][0])
			if self.history['playing_from_history'] == False:
				self.history['history'].append(self.next)
			return self.next


	def history_next_pos(self):
		old_pos = self.history['pos']
		self.history['pos'] = self.history['pos'] + 1
		if self.history['pos'] == len(self.history['history']):
			np.log("Reached end of history, disabing playing from history flag")
			self.history['pos'] = len(self.history['history']) - 1
			self.history['playing_from_history'] = False
		return self.history['pos']


	def history_prev_pos(self, pos=None):
		if pos == None:
			pos = self.history['pos']
		self.history['pos'] = pos
		old_pos = self.history['pos']
		self.history['pos'] = self.history['pos'] - 1
		if self.history['pos'] == -1:
			np.log("Reached beginning of history, resetting position to 0")
			self.history['pos'] = 0
		return self.history['pos']

	def skip_next(self):
		self.conf['nowplaying']['filepath'] = None
		self.conf['nowplaying']['play_pos'] = 0
		if self.play_mode == 'playlist':
			self.play()
			return True
		if self.history['playing_from_history'] == False:
			self.stop()
			if self.play_mode == 'database':
				self.next = self.get_next()
				self.play(self.next)
			elif self.play_mode == 'playlist':
				self.play()
			self.history['pos'] = len(self.history['history']) - 1
			np.log("skip_next, Not using history:" + str(self.history['history']))
		elif self.history['playing_from_history'] == True:
			try:
				#self.history['pos'] = self.history['history'].index(self.next)
				self.history['pos'] = self.history_next_pos()
				self.next = self.history['history'][self.history['pos']]
				
				np.log("skip_next: Using History at pos:" + str(self.history_pos) + ", " + self.next)
				self.play(self.next)
			except Exception as e:
				np.log("line 242: Reached end of playback history. Getting next from media list:" + str(e))
				self.history['playing_from_history'] = False
				self.history['pos'] = len(self.history['history']) - 1
				np.log("Reset history pos:" + str(self.history['pos']) + ", " + str(len(self.history['history'])))
				self.stop()
				self.next = self.get_next()
				self.play(self.next)


	def stop(self):
		self.player.stop()
		np.log("Playback stopped!")
		self.vlcInstance.release()
		#self.vlcInstance = None
		np.log("VLC Instance released!")
		self.media['is_playing'] = 0
		self.media['continuous'] = 0
		self.play_needed = 0
		self.media['now_playing'] = {}
		self.nowplaying['filepath'] = None


	def skip_previous(self):
		self.history['playing_from_history'] = True
		np.log("old history pos:" + str(self.history['pos']) + ", " + str(len(self.history['history'])))
		self.history['pos'] = self.history_prev_pos()
		#self.history['pos'] = self.history['history'].index(self.next) - 1
		np.log("new history pos:" + str(self.history['pos']) + ", " + str(len(self.history['history'])))
		try:
			self.next = self.history['history'][self.history['pos']]
		except:
			self.next = self.media['DBMGR_RESULTS'][self.history['pos']]
		if 'series:' in self.next:
			_id = self.next.split(':')[5]
			qstring = ("id = '" + _id + "'")
			self.next = np.querydb(table='series', column='filepath', query=qstring)[0][0]
		elif 'movies:' in self.next:
			_id = self.next.split(':')[3]
			qstring = ("id = '" + _id + "'")
			self.next = np.querydb(table='movies', column='filepath', query=qstring)[0][0]
		elif 'music:' in self.next:
			np.log("TODO: check playlist item string and parse out filepath!")
		np.log("Previous:" + self.next)
		self.play(self.next)


	def volume_set(self, vol):
		vol = int(vol)
		if vol <= 90:
			vol = vol + 10
		elif vol == 100 or vol >= 90:
			vol = 100
			np.log("Volume at max!")
		self.player.audio_set_volume(vol)
		self.conf['volume'] = vol


	def volume_up(self):
		vol = int(self.conf['volume'])
		if vol <= 90:
			vol = vol + 10
		elif vol == 100 or vol >= 90:
			vol = 100
			np.log("Volume at max!")
		self.player.audio_set_volume(vol)
		self.conf['volume'] = vol

	def volume_down(self):
		vol = int(self.conf['volume'])
		if vol >= 0:
			vol = vol - 10
		elif vol == 0 or vol <= 10:
			vol = 0
			np.log("Volume at zero!")
		self.player.audio_set_volume(vol)
		self.conf['volume'] = vol

	def seek_fwd(self):
		pos = self.player.get_position()
		if pos >= 0.992:
			pos = 0.99
		pos = pos + 0.007
		self.player.set_position(pos)
		
		
	def seek_rev(self):
		pos = self.player.get_position()
		if pos <= 0.008:
			pos = 0.0
		pos = pos - 0.007
		self.player.set_position(pos)

	
	def screenshot(self, c=0, n=None, w=None, h=None):
		if not os.path.exists(self.screencaps):
			try:
				pathlib.Path(self.screencaps).mkdir(parents=True, exist_ok=True)
			except Exception as e:
				np.log("Failed to create screencapture directory:" + str(e))
				return False
		screen = self.conf['screen']
		if n == None:
			jpgs = []
			files = [f for f in os.listdir(self.screencaps) if os.path.isfile(os.path.join(self.screencaps, f))]
			pos = -1
			for _file in files:
				if '.jpg' in _file:
					jpgs.append(_file)
			ct = (len(jpgs) + 1)
			n = (self.screencaps + os.path.sep + "nplayer.snapshot." + str(ct) + ".jpg")
			np.log("snapshot filename:" + str(n) + ", " + str(type(n)))
		if w == None:
			w = self.conf['windows']['viewer'][screen]['w']
		if h == None:
			h = self.conf['windows']['viewer'][screen]['h']
		try:
			ret = self.player.video_take_snapshot(c, n, w, h)
			if ret:
				np.log("nplayer snapshot return:" + str(ret))
				return True
		except Exception as e:
			np.log("failed to take snapshot:" + str(e))
			return ("failed to take snapshot:", e)


	def test_sftp(self):
		sftp_data_file = (np.SFTP_DIR + os.path.sep + 'info.txt')
		if not os.path.exists(sftp_data_file):
			return False
		else:
			return True


	def mount_sftp(self):
		user = conf['network_mode']['user']
		host = conf['network_mode']['host']
		sftp_data_file = (np.SFTP_DIR + os.path.sep + 'info.txt')
		try:
			com = ("sshfs '" + user + "@" + host + ":/var/storage' '" + np.SFTP_DIR + "'")
			ret = subprocess.check_output(com, shell=True).decode()
			if ret != '':
				np.log (("sftp mount returned value:" + ret), 'error')
			line=(user + '@' + host)
			with open(sftp_data_file, 'w') as f:
				f.write(line)
				f.close()
			with open(sftp_data_file, 'r') as f:
				user_host = f.read().strip()
			return True
		except Exception as e:
			txt = ("Unable to mount sftp:" + str(e))
			np.log(txt, 'error')
			return False

	
	def play(self, _file=None):
		if self.next is not None and self.play_mode == 'playlist':
			self.playlist_last = self.next
		if self.play_mode == 'database':
			if _file is None and self.conf['nowplaying']['filepath'] is None:
				np.log("File and resume is None, getting next...")
				self.next == self.get_next()
				self.play_pos = 0
			elif _file is None and self.conf['nowplaying']['filepath'] is not None:
				np.log("Resuming playback...")
				self.next = str(self.conf['nowplaying']['filepath'])
				if 'series:' in self.next:
					_id = self.next.split(':')[5]
					qstring = ("id = '" + _id + "'")
					self.next = np.querydb(table='series', column='filepath', query=qstring)[0][0]
				elif 'movies:' in self.next:
					_id = self.next.split(':')[3]
					qstring = ("id = '" + _id + "'")
					self.next = np.querydb(table='movies', column='filepath', query=qstring)[0][0]
				elif 'music:' in self.next:
					np.log("TODO: check playlist item string and parse out filepath!")
				self.selected_playlist_item = self.get_info_string(self.next)
				self.play_pos = float(self.conf['nowplaying']['play_pos'])
				self.conf['nowplaying']['filepath'] = None
				np.log('set nowplaying filepath to None...')
				np.writeConf(self.conf)
			else:
				np.log("File path provided, setting as next:" + _file)
				self.next = _file
				self.selected_playlist_item = self.get_info_string(self.next)
				self.play_pos = 0
				self.conf['nowplaying']['filepath'] = self.next
				self.conf['nowplaying']['play_pos'] = self.play_pos
				np.writeConf(self.conf)
		elif self.play_mode == 'playlist':
			if _file is None and self.conf['nowplaying']['filepath'] is None:
				self.next = self.get_playlist_next()
				np.log("Playlist: Getting next:" + self.next)
				self.play_pos = 0
				self.playlist_last = self.next
				self.conf['nowplaying']['filepath'] = self.next
				self.conf['nowplaying']['play_pos'] = self.play_pos
			elif _file is None and self.conf['nowplaying']['filepath'] is not None:
				self.playlist_last = self.next
				self.next = str(self.conf['nowplaying']['filepath'])
				np.log("Playlist: Resuming from nowplaying:" + self.next)
				if 'series:' in self.next:
					_id = self.next.split(':')[5]
					qstring = ("id = '" + _id + "'")
					self.next = np.querydb(table='series', column='filepath', query=qstring)[0][0]
				elif 'movies:' in self.next:
					_id = self.next.split(':')[3]
					qstring = ("id = '" + _id + "'")
					self.next = np.querydb(table='movies', column='filepath', query=qstring)[0][0]
				elif 'music:' in self.next:
					np.log("TODO: check playlist item string and parse out filepath!")
				self.selected_playlist_item = self.get_info_string(self.next)
				self.play_pos = float(self.conf['nowplaying']['play_pos'])
				self.conf['nowplaying']['filepath'] = None
				np.log('set nowplaying filepath to None...')
				np.writeConf(self.conf)
			else:
				np.log("Playlist: File provided:" + _file)
				self.playlist_last = self.next
				self.next = _file
				self.selected_playlist_item = self.get_info_string(self.next)
				self.play_pos = 0
				self.conf['nowplaying']['filepath'] = self.next
				self.conf['nowplaying']['play_pos'] = self.play_pos
				np.writeConf(self.conf)
		if self.vlcInstance is None:
			try:
				opts = self.conf['vlc']['opts']
			except:
				opts = "--no-xlib"
			self.vlcInstance = vlc.Instance(opts)
			self.player = self.vlcInstance.media_player_new()
		if self.conf['network_mode']['mode'] == 'remote' and '/.np/sftp' not in self.next:
			is_mounted = self.test_sftp()
			if not is_mounted:
				self.mount_sftp()
			fpath = self.next.split('/var/storage/')[1]
			self.next = (np.SFTP_DIR + os.path.sep + fpath)
			#self.next = ('/run/user/1000/gvfs/sftp:host=' + host + ',user=' + user + self.next)
			print ("Network uri:", self.next)
		try:
			self.media['current_vlc_media_object'] = self.vlcInstance.media_new_path(self.next)
			self.player.set_media(self.media['current_vlc_media_object'])
			self.player.play()
			self.is_url = False
		except Exception as e:
			txt = ("Unable to open media item:" + e + ", filepath=" + self.next)
			np.log(txt, 'error')
			if self.conf['network_mode']['mode'] == 'remote':
				self.mount_sftp()
				self.media['current_vlc_media_object'] = self.vlcInstance.media_new_path(self.next)
				self.player.set_media(self.media['current_vlc_media_object'])
				self.player.play()
				self.is_url = False
		if self.play_pos >= 0:
			self.player.set_position(self.play_pos)
		self.media['continuous'] = 1
		if self.conf['play_type'] == 'series' or  self.conf['play_type'] == 'movies':
			if self.is_url == False:
				time.sleep(0.5)
				self.scale = np.calculate_scale(self.next)
				if self.scale == None:
					self.scale_needed = 0
				else:
					self.player.video_set_scale(self.scale)
					test_scale = self.player.video_get_scale()
					if test_scale:
						self.scale_needed = 1
		self.volume = self.player.audio_get_volume()
		self.media['is_playing'] = self.player.is_playing()
		if self.media['is_playing'] == 1 or self.media['is_playing'] == True:
			self.media['now_playing']['filepath'] = self.next
			self.play_needed = 0
			np.log("Set play needed: 0")
		if self.conf['play_type'] == 'series':
			try:
				query_string = ("filepath like '%" + self.next + "%'")
				series_name = np.querydb('series', 'series_name', query_string)[0][0]
				np.log("Series name:" + series_name)
				self.series_history[series_name] = self.next
				np.write_history(self.series_history)
			except:
				pass
		elif self.conf['play_type'] == 'music':
			try:
				self.album_art = self.dl_img()
				self.ART_UPDATE_NEEDED = True
			except:
				self.ART_UPDATE_NEEDED = False
		self.conf['nowplaying']['filepath'] = self.next

	def dl_img(self, filepath=None):
		if filepath is None:
			filepath = self.next
		test='https://www.google.com/imgres?imgurl='
		s = '&amp;imgrefurl'
		song = eyed3.load(filepath)
		artist = song.tag.artist
		title = song.tag.title
		query = (artist + " " + title + " album art")
		q = quote(query)
		url = ("https://www.google.com/search?q=" + q)
		r = requests.get(url)
		data = r.text.split("\n")
		for item in data:
			if test in item:
				self.img_url = item.split(test)[1].split(s)[0]
				if '%' in self.img_url:
					self.img_url = unquote(self.img_url)
				break
		com = ("wget --output-document 'poster.jpg' '" + self.img_url + "'")
		subprocess.check_output(com, shell=True)
		screen = self.conf['screen']
		self.art_w = self.conf['windows']['viewer'][screen]['w']
		self.art_h = self.conf['windows']['viewer'][screen]['h']
		com = ("convert 'poster.jpg' -resize " + str(self.art_w) + "x" + str(self.art_h) + " 'poster.png'")
		ret = subprocess.check_output(com, shell=True)
		self.album_art = 'poster.png'
		return self.album_art


	def load_playlist(self, filepath):
		try:
			results = []
			with open(filepath, 'r') as f:
				lines = f.read().strip().split("\n")
			f.close()
			return lines
		except Exception as e:
			np.log("Unable to load media playlist:" + str(e) + ", " + filepath)
			return None


	def save_playlist(self, filepath, media_list):
		try:
			j = "\n"
			data = j.join(media_list)
			with open(filepath, 'w') as f:
				f.write(data)
			f.close()
			return True
		except Exception as e:
			np.log("Unable to save media playlist:" + str(e) + ", " + filepath + ", " + str(media_list))
			return False

	def load_directory(self, path):
		try:
			com = ("mkmedialist '" + path + "'")
			playlist = subprocess.check_output(com, shell=True)
			items = self.load_playlist(playlist)
			return items
		except Exception as e:
			np.log("Unable to load directory:" + str(e) + ", " + path)
			return None


	def build_info_string_from_filepath(self, filepath):
		np.log("running build info from filepath")
		qstring = ("filepath = '" + filepath + "'")
		try:
			series_name, season, episode_number, episode_name, _id = np.querydb('series', 'series_name,season,episode_number,episode_name,id', qstring)[0]
			sstring = ("series:" + series_name + ":" + str(season) + ":" + str(episode_number) + ":" + episode_name + ":" + str(_id))
			np.log("Series string:" + sstring)
		except:
			sstring = None
		try:
			title, year, _id = np.querydb('movies', 'title,year,id', qstring)[0]
			mvstring = ("movies:" + title + ":" + str(year) + ":" + str(_id))
			np.log("Movies string:" + mvstring)
		except:
			mvstring = None
		try:
			msstring = np.querydb('music', 'filepath', qstring)[0]
		except:
			msstring = None
		if sstring is not None:
			return sstring
		elif mvstring is not None:
			return mvstring
		elif msstring is not None:
			return msstring
		else:
			np.log("data not found in database:" + filepath)
			return None


	def get_playlist_next(self):
		self.play_mode = 'playlist'
		items = self.media['DBMGR_RESULTS']
		np.log("DBMGR_RESULTS/items:" + str(items))
		idx = None
		if self.playlist_last is None:
			try:
				self.next = items[0]
			except Exception as e:
				np.log("Playlist appears empty!" + str(e))
				self.play_mode = 'database'
				return None
		else:
			if self.playlist_loop_one == True:
				self.next = self.playlist_last
				return self.next
			else:
				self.playlist_last = self.next
			#try:

				if 'series:' in self.playlist_last or 'movies:' in self.playlist_last or 'music:' in self.playlist_last:
					string = self.build_info_string_from_filepath(self.playlist_last)
					idx = items.index(string)
				else:
					string = self.playlist_last
					try:
						idx = items.index(string)
					except:
						query_string = ("filepath = '" + string + "'")
						inseries, inmovies, inmusic = None, None, None
						try:
							inseries = np.querydb(table='series', column='filepath', query=query_string)[0]
						except:
							pass
						try:
							inmovies = np.querydb(table='movies', column='filepath', query=query_string)[0]
						except:
							pass
						try:
							inmusic = np.querydb(table='music', column='filepath', query=query_string)[0]
						except:
							pass
						if inseries is not None:
							series_name, season, episode_number, episode_name, _id = np.querydb(table='series', column='series_name,season,episode_number,episode_name,id', query=query_string)[0]
							string = ('series:' + series_name + ":" + str(season) + ":" + str(episode_number) + ":" + str(episode_name) + ":" + str(_id))
							idx = items.index(string)
							#'series:Rick and Morty:5:1:Mort Dinner Rick Andre:1199'
						elif inmovies is not None:
							title, year, _id = np.querydb(table='movies', column='title,year,id', query=query_string)[0]
							string = ("movies:" + title + ":" + str(year) + ":" + str(_id))
							idx = items.index(string)
						elif inmusic is not None:
							table = 'music'


				try:
					idx = idx + 1
					self.history['pos'] = idx
					self.next = items[idx]
					self.history['history'].append(self.next)
				except:
					if self.playlist_loop_all == True:
						self.next = items[0]
						self.history['history'] = [self.next]
						self.history['pos'] = 0
					else:
						self.playlist_mode = 'database'
						self.next = None
						return False
			#except Exception as e:
			#	np.log("Unable to get next:" + str(idx) + ", " + str(e))
			#	self.play_mode = 'database'
			#	return None
		if 'series:' in self.next:
			_id = self.next.split(':')[5]
			qstring = ("id = '" + _id + "'")
			self.next = np.querydb(table='series', column='filepath', query=qstring)[0][0]
		elif 'movies:' in self.next:
			_id = self.next.split(':')[3]
			qstring = ("id = '" + _id + "'")
			self.next = np.querydb(table='movies', column='filepath', query=qstring)[0][0]
		elif 'music:' in self.next:
			np.log("TODO: check playlist item string and parse out filepath!")

		return self.next
	
