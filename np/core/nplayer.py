import pathlib
import os
import pafy
from PIL import Image, ImageTk
import requests
import subprocess
import eyed3
import urllib
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
		
		try:
			self.main_keyboard = self.conf['main_keyboard']['path']
		except:
			self.main_keyboard = None


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
			#print ("seek_to_pos, line 236", e)
			return 1


	def playback_started(self):
		self.media['is_playing'] = 1
		self.play_needed = 0
	
	def playback_finished(self):
		print ("Playback finished!")
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
						#print ("Plaback nearly ending...")
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
					print ("Uh, oh... spaghetti ohs.")
				elif event == 'EventType.MediaMPVout':
					pass
				elif event == 'EventType.MediaMPChapterChanged':
					self.chapter = self.player.get_chapter()
					print ("Chapter changed:", self.chapter)
				else:
					print ("VLC Event callback running:", event)


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
			#print ("get next: series started!")
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
				#print ("Last in list:", self.last)
				idx = int(_list.index(self.last))
				idx = idx + 1
				try:
					self.next = _list[idx]
					self.selected_playlist_item = self.get_info_string(self.next)
				#	print ("Next set! Series Name, Index, Next:", series_name, idx, self.next)
				except:
					self.next = _list[0]
					self.selected_playlist_item = self.get_info_string(self.next)
				#	print ("Next not set (reset to 0)! Series Name, Index, Next:", series_name, idx, self.next)
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
				txt = "Last file recorded not in playlist:", self.last, _list
				np.write_log (str(txt), 'error')
			#except Exception as e:
				#print ("line 214,", e)
			#	self.next = np.querydb(table='series', column='filepath', query=qstring)[0][0]
			#	if self.history['playing_from_history'] == False:
			#		self.history['history'].append(self.next)
			#	self.series_history[series_name] = self.next
			#	np.write_history(self.series_history)
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
		#print ("history position changed:", old_pos, self.history['pos'])
		if self.history['pos'] == len(self.history['history']):
			#print ("Reached end of history, disabing playing from history flag")
			self.history['pos'] = len(self.history['history']) - 1
			self.history['playing_from_history'] = False
		return self.history['pos']


	def history_prev_pos(self):
		old_pos = self.history['pos']
		self.history['pos'] = self.history['pos'] - 1
		#print ("history position changed:", old_pos, self.history['pos'])
		if self.history['pos'] == -1:
			#print ("Reached beginning of history, resetting position to 0")
			self.history['pos'] = 0
		return self.history['pos']

	def skip_next(self):
		print ("old history pos:", self.history['pos'], len(self.history['history']))
		if self.history['playing_from_history'] == False:
			self.stop()
			self.next = self.get_next()
			self.play(self.next)
			self.history['pos'] = len(self.history['history']) - 1
			#print ("new history pos:", self.history['pos'], len(self.history['history']))
			#print ("skip_next, Not using history:", self.history['history'])
		elif self.history['playing_from_history'] == True:
			try:
				#self.history['pos'] = self.history['history'].index(self.next)
				self.history['pos'] = self.history_next_pos()
				self.next = self.history['history'][self.history['pos']]
				
				#print ("skip_next: Using History at pos:", self.history_pos, self.next)
				self.play(self.next)
			except Exception as e:
				#print ("line 242: Reached end of playback history. Getting next from media list...", e)
				self.history['playing_from_history'] = False
				self.history['pos'] = len(self.history['history']) - 1
				#print ("Reset history pos:", self.history['pos'], len(self.history['history']))
				self.stop()
				self.next = self.get_next()
				self.play(self.next)


	def stop(self):
		self.player.stop()
		print ("Playback stopped!")
		self.vlcInstance.release()
		#self.vlcInstance = None
		print ("VLC Instance released!", self.vlcInstance)
		self.media['is_playing'] = 0
		self.media['continuous'] = 0
		self.play_needed = 0
		self.media['now_playing'] = {}
		self.nowplaying['filepath'] = None


	def skip_previous(self):
		self.history['playing_from_history'] = True
		#print ("old history pos:", self.history['pos'], len(self.history['history']))
		self.history['pos'] = self.history_prev_pos()
		#self.history['pos'] = self.history['history'].index(self.next) - 1
		#print ("new history pos:", self.history['pos'], len(self.history['history']))
		self.next = self.history['history'][self.history['pos']]
		#print ("Previous:", self.next)
		self.play(self.next)


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
				print ("Failed to create screencapture directory:", e)
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
			print ("snapshot filename:", n, type(n))
		if w == None:
			w = self.conf['windows']['viewer'][screen]['w']
		if h == None:
			h = self.conf['windows']['viewer'][screen]['h']
		try:
			ret = self.player.video_take_snapshot(c, n, w, h)
			if ret:
				print (ret)
				return True
		except Exception as e:
			print ("failed to take snapshot:", e)
			return ("failed to take snapshot:", e)


	def screencap(self, filename=None, screen=None, fps=24, vcodec='h264', vid_bitrate=0, scale=0, acodec='mp4a', aud_bitrate=128, chnls=2, smplrt=44100):
		if filename == None:
			vids = []
			files = [f for f in os.listdir(self.screencaps) if os.path.isfile(os.path.join(self.screencaps, f))]
			pos = -1
			for _file in files:
				if '.mp4' in _file:
					vids.append(_file)
			ct = (len(vids) + 1)
			n = (self.screencaps + os.path.sep + "nplayer.screencap." + str(ct) + ".mp4")
			print ("capture filename:", n, type(n))
		if screen == None:
			screen = 'screen://'
		else:
			screen = ('screen://' + str(screen))
		fps = (":screen-fps=" + str(fps))
		sout = (":sout=#transcode{vocdec=" + str(vcodec) + ",vb=" + str(vid_bitrate) + ",scale=" + str(scale) + ",acodec=" + str(acodec) + ",ab=" + str(aud_bitrate) + ",channels=" + str(chnls) + ",samplerate=" + str(smplrt) + "}:file{dst=" + n + "}")
		args = ('"' + screen + '","' + fps + '","' + sout + '",":sout-keep"')
		try:
			m = self.vlcInstance.media_new(args)
			self.player.set_media(m)
			self.player.play()
			print ("Screen capture running!")
			self.is_recording = True
		except Exception as e:
			print ("Unable to start capture! Data:", e, args)
			self.is_recording = False
		return self.is_recording
	
	def play(self, _file=None):
		if _file is None and self.conf['nowplaying']['filepath'] is None:
			#print ("File and resume is None, getting next...")
			self.next = self.get_next()
			self.play_pos = 0
		elif _file is None and self.conf['nowplaying']['filepath'] is not None:
			#print ("Resuming playback...")
			self.next = str(self.conf['nowplaying']['filepath'])
			self.selected_playlist_item = self.get_info_string(self.next)
			self.play_pos = float(self.conf['nowplaying']['play_pos'])
			self.conf['nowplaying']['filepath'] = None
			#print ('set nowplaying filepath to None...')
			np.writeConf(self.conf)
		else:
			#print ("File path provided, setting as next")
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
			#print ("Set play needed: 0")
		if self.conf['play_type'] == 'series':
			try:
				print ("Next:", self.next)
				query_string = ("filepath like '%" + self.next + "%'")
				series_name = np.querydb('series', 'series_name', query_string)[0][0]
				#print ("Series name:", series_name)
				self.series_history[series_name] = self.next
				np.write_history(self.series_history)
			except:
				pass
		elif self.conf['play_type'] == 'music':
			print ("line 335, play(), Insert album art grabber/display block here")
		self.conf['nowplaying']['filepath'] = self.next
		if self.conf['play_type'] == 'music':
			self.album_art = self.dl_img()
			self.ART_UPDATE_NEEDED = True


	def dl_img(self, query_string=None):
		if query_string is None:
			filepath = self.conf['nowplaying']['filepath']
			if filepath is not None:
				print ("filepath:", filepath, type(filepath))
				filepath = urllib.parse.unquote(filepath)
				if self.conf['play_type'] == 'music':
					a = eyed3.load(filepath)
					artist = a.tag.artist
					title = a.tag.title
					query_string = (artist + " " + title)
				
		api_key = '482f3866594242e97dcc1573601a9fb13b4345479d97b4ef03e1b7a76523a58d'
		query_string = urllib.parse.quote(query_string)
		url = ("https://serpapi.com/search.json?q=" + query_string + "&tbm=isch&ijn=0&api_key=" + str(api_key))
		r = requests.get(url)
		json_data = json.loads(r.text)
		self.img_url = json_data['images_results'][0]['original']

		com = ("wget --output-document 'poster.jpg' '" + self.img_url + "'")
		subprocess.check_output(com, shell=True)
		screen = self.conf['screen']
		self.art_w = self.conf['windows']['viewer'][screen]['w']
		self.art_h = self.conf['windows']['viewer'][screen]['h']
		com = ("convert 'poster.jpg' -resize " + str(self.art_w) + "x" + str(self.art_h) + " 'poster.png'")
		ret = subprocess.check_output(com, shell=True)
		self.album_art = 'poster.png'
		return self.album_art
