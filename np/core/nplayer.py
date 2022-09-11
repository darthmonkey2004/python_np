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
		self.create_media = np.create_media
		self.conf = {}
		self.conf['vlc'] = {}
		try:
			self.conf = np.readConf()
		except Exception as e:
			np.log(f"Exception reading conf file: will wipe the stored window locations... {e}", 'warning')
			self.conf = np.initConf()
			self.conf['windows'] = np.init_window_position()
		self.conf['grab_devices'] = ['/dev/input/event11']
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
		np.log(f"play_needed set = 1: line46", 'info')
		self.scale_needed = 0
		self.PLAYLIST_ITEMS = self.media['PLAYLIST_ITEMS']
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
		self.remote_media = []
		self.exit = False
		self.conf['intro'] = {}
		self.conf['intro']['start'] = None
		self.conf['intro']['end'] = None
		self.intro_start = None
		self.intro_end = None
		self.continuous = 1
		self.is_playing = 0
		self.series_history = np.read_history()
		self.resume = None
		self.play_pos = self.conf['nowplaying']['play_pos']
		self.server = None
		


	def get_position(self):
		return self.player.get_position()


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
		self.is_playing = 1
		self.play_needed = 0

	def playback_finished(self):
		np.log("Playback finished!")
		self.nowplaying['filepath'] = None
		self.play_needed = 1
		np.log(f"play_needed set = 1 (playback_finished): line123", 'info')

	def init_vlc(self, uri=None):
		try:
			opts = self.conf['vlc']['opts']
		except:
			opts = "--no-xlib"
		self.vlcInstance = vlc.Instance(opts)
		np.log(f"nplayer.py, init_vlc(): Instance created! Options: {opts}", 'info')
		if uri == None:
			self.player = self.vlcInstance.media_player_new()
		else:
			self.player = self.vlcInstance.media_player_new(uri)
		self.player.audio_set_mute(self.conf['mute'])
		if self.conf['mute'] == False:
			self.player.audio_set_volume(self.conf['volume'])
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
		np.log(f"nplayer.py, set_now_playing: play_pos set={self.conf['nowplaying']['filepath']}", 'info')
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
					np.log(f"play_needed set = 1 (vlc_event[MediaMPEndReached]): line169, conf written", 'info')
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
					self.is_playing = self.player.is_playing()
					self.play_needed = 0
					np.log(f"play_needed set = 0 (vlc_event[MediaMPPlaying]: line202", 'info')
				elif event == 'EventType.MediaMPAudioDevice':
					self.audio_device = self.player.audio_output_device_get()
				elif event == 'EventType.MediaMPAudioVolume':
					self.nowplaying['volume'] = self.player.audio_get_volume()
				elif event == 'EventType.MediaMPStopped':
					self.nowplaying['is_playing'] = self.player.is_playing()
					self.is_playing = 0
				elif event == 'EventType.MediaMPEncounteredError':
					pass
				elif event == 'EventType.MediaMPVout':
					pass
				elif event == 'EventType.MediaMPChapterChanged':
					self.chapter = self.player.get_chapter()
				else:
					pass


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
			self.series_history = np.read_history()
			try:
				self.last = self.series_history[series_name]
			except:
				self.last = None
			if self.last in _list and self.last is not None:
				if self.conf['debug'] == True:
					np.log("Last in list: {self.last}", 'info')
				idx = int(_list.index(self.last))
				idx = idx + 1
				try:
					self.next = _list[idx]
					self.selected_playlist_item = self.get_info_string(self.next)
					np.log(f"get_next:Next set! Series Name: {series_name}, Index: {idx}, Next: {self.next}", 'info')
				except:
					self.next = _list[0]
					self.selected_playlist_item = self.get_info_string(self.next)
					np.log(f"get_next:Next not set (reset to 0)! Series Name: {series_name}, Index: {idx}, Next: {self.next}", 'info')
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
			if self.conf['debug'] == True:
				np.log(f"DEBUG=True:get_next exited. next={self.next}", 'info')
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
		np.log(f"nplayer.py, skip_next: blanked nowplaying info (None, 0)", 'info')
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
			if self.conf['debug'] == True:
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
		np.log("VLC Instance released!")
		self.is_playing = 0
		self.continuous = 0
		self.play_needed = 0
		np.log(f"play_needed set = 0 (stop): line361", 'info')
		self.media['now_playing'] = {}
		self.nowplaying['filepath'] = None


	def skip_previous(self):
		self.history['playing_from_history'] = True
		np.log(f"old history pos:Position={self.history['pos']}, Length={len(self.history['history'])}", 'info')
		self.history['pos'] = self.history_prev_pos(self.history['pos'])
		#self.history['pos'] = self.history['history'].index(self.next) - 1
		np.log(f"new history pos:Position={self.history['pos']}, Length={len(self.history['history'])}", 'info')
		try:
			self.next = self.history['history'][self.history['pos']]
			np.log(f"self.next set from history index({self.history['pos']}):{self.next}", 'info')
		except Exception as e:
			self.next = self.media['PLAYLIST_ITEMS'][self.history['pos']]
			np.log(f"Error setting next from history: {e}, next='{self.next}'", 'error')
		
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
		try:
			vol = int(vol)
			if vol <= 90:
				vol = vol + 10
			elif vol == 100 or vol >= 90:
				vol = 100
				np.log("Volume at max!")
			self.player.audio_set_volume(vol)
			self.conf['volume'] = vol
			return True
		except Exception as e:
			np.log(f"Error: Bad volume! Bad! Details: {e}", 'error')
			return False


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

	
	def screenshot(self, src=0, dest_dir=None, w=0, h=0):
		ts = time.time()
		if dest_dir == None:
			dest_dir = f"{np.DATA_DIR}/cap.{ts}.png"
		try:
			if self.conf['debug'] == True:
				np.log(f"snapshot: out_dir:{dest_dir}, w:{w}, h:{h}", 'info')
			ret = self.player.video_take_snapshot(src, dest_dir, w, h)
			if ret:
				np.log(f"nplayer snapshot return:{ret}", 'info')
				return True
		except Exception as e:
			np.log(f"failed to take snapshot:{e}", 'error')
			return False


	def constrain_scale(self, scale):
		if scale >= 10:
			return float(scale / 100)#Convert to 1-10 float value if in percentage
		else:
			return float(scale)#force to float if already in 1-10 scale

	def set_scale(self, filepath=None):
		if filepath == None:
			filepath = self.next
			np.log(f"set_scale: Filepath not provided, using self.next ({self.next}).", 'info')
		else:
			np.log(f"set scale: Filepath provided: {filepath}", 'info')
		prescale = self.player.video_get_scale()
		scale = np.calculate_scale(filepath)
		scale = self.constrain_scale(scale)
		self.player.video_set_scale(scale)
		if prescale != scale:
			self.scale_needed = 1
			np.log(f"Calculated scale != set scale, setting scale_needed=1.  Previous:{prescale}, Set:{scale}", 'info')
		elif prescale == scale:
			np.log(f"Scales match, skipping scale_needed. Previous:{prescale}, New:{scale}", 'info')
			self.scale_needed = 0
		self.scale = scale

						

	def play(self, _file=None):
		print(self.play_mode)
		#init resume to None
		self.resume = None
		self.series_history = np.read_history()
		#init next to None
		self.next = None
		#if filepath provided...
		if _file is not None:
			self.next = _file
			np.log(f"File provided: {self.next}. Set as next...", 'info')
		#else if resume from file...
		elif _file is None and self.conf['nowplaying']['filepath'] is not None:
			if self.conf['nowplaying']['play_pos'] is not None:
				self.play_pos = self.conf['nowplaying']['play_pos']
			else:
				self.play_pos = 0
			self.next = self.conf['nowplaying']['filepath']
			np.log(f"Resuming from file (nowplaying): {self.next}. Set as next...", 'info')
		#if next is set, check if remains of playlist mode in next string...
		if self.next is not None:
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
			#test type vs file string
			play_type = self.conf['play_type']
			if play_type == 'series' or play_type == 'movies':
				if self.conf['media_directories']['music'] in self.next:
					self.next = None
					np.log("Stale type found as filepath. Setting as None...", 'info')
		# if next is not set...
		if self.next is None:
			#if mode is  playlist
			if self.play_mode == 'playlist':
				self.next = self.get_playlist_next()
				self.play_pos = 0
				np.log(f"Playlist: Getting next:{self.next}", 'info')
			elif self.play_mode == 'database':
				self.next = self.get_next()
				self.play_pos = 0
				np.log(f"Database: Getting next:{self.next}", 'info')
		#By this point, next should be set.
		if self.play_mode == 'playlist':
			self.playlist_last = self.next
			self.selected_playlist_item = self.get_info_string(self.next)
			l = len(list(self.history.values()))
			self.history[l] = self.playlist_last
			if self.conf['debug'] == True:
				np.log(f"playlist last set in MP.play(): playlist_last:{self.playlist_last}, play_mode={self.play_mode}", 'info')
			if self.conf['play_type'] == 'series':
				try:
					query_string = ("filepath like '%" + self.next + "%'")
					series_name = np.querydb('series', 'series_name', query_string)[0][0]
					self.series_history[series_name] = self.next
					np.write_history(self.series_history)
				except:
					np.log(f"Couldn't find series db or history...(playlist?)", 'info')

		elif self.play_mode == 'database':
			series_name = None		
			if self.conf['play_type'] == 'series':
				try:
					query_string = ("filepath like '%" + self.next + "%'")
					np.log(f"Query string: {query_string}", 'info')
					series_name = np.querydb('series', 'series_name', query_string)[0][0]
					self.series_history[series_name] = self.next
					np.write_history(self.series_history)
				except:
					pass

		#Guess intro
		intro = np.guess_intro(self.next)
		if intro is not None:
			self.conf['intro'] = {}
			self.conf['intro']['start'] = intro[0]
			self.conf['intro']['end'] = intro[1]
			np.log(f"Intro detected! Start={intro[0]}, End={intro[1]}", 'info')
		else:
			self.conf['intro'] = {}
			self.conf['intro']['start'] = None
			self.conf['intro']['end'] = None
			np.log("No intro found for '{self.next}'", 'info')
		# check for vlc instance
		if self.vlcInstance is None:
			try:
				opts = self.conf['vlc']['opts']
			except:
				opts = "--no-xlib"
			self.vlcInstance = vlc.Instance(opts)
			np.log(f"nplayer.py, play(): Instance created! Options: {opts}", 'info')
			self.player = self.vlcInstance.media_player_new()
		# check if network mode is remote:
		if self.conf['network_mode']['media_mode'] == 'remote':
			#test if sftp is mounted
			is_mounted = self.test_sftp()
			if not is_mounted:
				#mount if necessary
				self.mount_sftp()
			# test if remote uri in next string
			if '/.np/sftp' not in self.next:
				fpath = self.next.split(np.MEDIA_DIR)[1]
				self.next = (np.SFTP_DIR + os.path.sep + fpath)
				np.log(f"Network uri set:{self.next}", 'info')
		# attempt to set media path.
		try:
			self.media['current_vlc_media_object'] = self.vlcInstance.media_new_path(self.next)
			self.player.set_media(self.media['current_vlc_media_object'])
			self.player.play()
			self.is_url = False
		except Exception as e:
			np.log(f"Unable to open media item:{e}, filepath={self.next}", 'error')
			if self.conf['network_mode']['media_mode'] == 'remote':
				self.mount_sftp()
				self.media['current_vlc_media_object'] = self.vlcInstance.media_new_path(self.next)
				self.player.set_media(self.media['current_vlc_media_object'])
				self.player.play()
				self.is_url = False
		# set play position if greater than 0
		if self.play_pos >= 0:
			self.player.set_position(self.play_pos)
			self.play_pos = 0
			self.conf['nowplaying']['play_pos'] = 0
		self.continuous = 1
		if self.conf['play_type'] == 'series' or  self.conf['play_type'] == 'movies':
			if self.is_url == False:
				if self.next is not None:
					self.set_scale(self.next)
				else:
					np.log(f"WARNING:next not set! {self.next}. Retrying...", 'warning')
					self.next == self.get_next()
					ret = self.scale(self.next)
		#set volume
		self.volume = self.player.audio_get_volume()
		self.is_playing = self.player.is_playing()
		if self.is_playing == 1 or self.is_playing == True:
			self.conf['nowplaying']['filepath'] = self.next
			self.conf['nowplaying']['play_pos'] = self.play_pos
			self.play_needed = 0
			np.log("Set play needed = 0 (play): line624", 'info')

		if self.conf['play_type'] == 'music':
			#try:
			self.album_art = self.dl_img()
			self.ART_UPDATE_NEEDED = True
			#except:
			#	self.ART_UPDATE_NEEDED = False

		np.writeConf(self.conf)


	def dl_img(self, filepath=None):
		if filepath is None:
			filepath = self.next
		test='https://www.google.com/imgres?imgurl='
		s = '&amp;imgrefurl'
		song = np.tag().read(filepath)
		artist = song.artist
		title = song.title
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
		try:
			com = ("wget --output-document 'poster.jpg' '" + self.img_url + "'")
			subprocess.check_output(com, shell=True)
		except Exception as e:
			np.log(f"Unable to get poster: {e}", 'error')
		screen = self.conf['screen']
		self.art_w = self.conf['windows']['viewer'][screen]['w']
		self.art_h = self.conf['windows']['viewer'][screen]['h']
		com = ("convert 'poster.jpg' -resize " + str(self.art_w) + "x" + str(self.art_h) + " 'poster.png'")
		ret = subprocess.check_output(com, shell=True)
		self.album_art = 'poster.png'
		return self.album_art


	def load_playlist(self, filepath):
		if self.conf['network_mode']['media_mode'] == 'remote':
			fpath = filepath.split('/var/storage/')[1]
			filepath = (np.SFTP_DIR + os.path.sep + fpath)
		if os.path.exists(filepath):
			try:
				results = []
				with open(filepath, 'r') as f:
					lines = f.read().strip().split("\n")
				f.close()
				return lines
			except Exception as e:
				np.log("Unable to load media playlist:" + str(e) + ", " + filepath)
				return None
		else:
			np.log("Playlist file does not exist! '{filepath}'", 'error')
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
			np.log(f"Unable to save media playlist:{e}, {filepath}, {media_list}", 'error')
			return False

	def load_directory(self, path):
		try:
			com = (f"mkmedialist '{path}'")
			ret = subprocess.check_output(com, shell=True).decode().strip()
			if ret:
				np.log(f"Error: {ret}", 'error')
			playlist = (f"{path}{os.path.sep}medialist.txt")
			items = self.load_playlist(playlist)
			return items
		except Exception as e:
			np.log(f"Unable to load directory:({e}), {path}", 'error')
			return None


	def build_info_string_from_filepath(self, filepath):
		try:
			np.log("running build info from filepath")
			qstring = ("filepath = '" + filepath + "'")
			try:
				series_name, season, episode_number, episode_name, _id = np.querydb('series', 'series_name,season,episode_number,episode_name,id', qstring)[0]
				sstring = (f"series:{series_name}:{season}:{episode_number}:{episode_name}:{_id}")
				np.log(f"Series string:{sstring}", 'info')
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
				np.log(f"data not found in database: {filepath}", 'info')
				return None
		except:
			np.log(f"data not found in database: {filepath}", 'info')


	def get_playlist_next(self):
		self.play_mode = 'playlist'
		items = self.media['PLAYLIST_ITEMS']
		np.log(f"PLAYLIST_ITEMS/items:{items}", 'info')
		idx = None
		if self.playlist_last is None:
			try:
				self.next = items[0]
				np.log(f"Playlist next set to 0: {self.next}", 'info')
			except Exception as e:
				np.log(f"Playlist appears empty!{e}", 'error')
				self.play_mode = 'database'
				return None
		else:
			if self.playlist_loop_one == True:
				self.next = self.playlist_last
				if self.conf['debug'] == True:
					np.log(f"Playlist next is playlist last, loop_one=True.", 'info')
				return self.next
			else:
				self.playlist_last = self.next
				np.log(f"self.playlist_last:{self.playlist_last}", 'debug')
				string = self.build_info_string_from_filepath(self.playlist_last)
				if self.conf['debug'] == True:
					np.log(f"Built playlist parse string from filepath. string={string}, filepath='{self.playlist_last}'", 'info')
				try:
					idx = items.index(string)
					np.log(f"Index set from string: {idx}, {string}", "info")
				except Exception as e:
					idx = 1
					np.log(f"Exception setting index with string {string}:{e}", 'error')
				query_string = (f"filepath = '{string}'")
				np.log(f"Query string:{query_string}", 'debug')
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
	
