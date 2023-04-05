import time
from np.utils.pbdl.utils import test_media
from np.utils.searchdb import querydb
from np.utils.id3 import tag
from np.core.log import np_logger
from np.core.playlist import *
from np.core.conf import readConf, initConf
from np.core.playlist import *
from np.core.core import read_history, write_history, calculate_scale
from np.utils.guess_intro import guess_intro
import vlc
from urllib.parse import quote, unquote
import requests

log = np_logger().log_msg

#-------------main player class=------------#
class nplayer():
	def __init__(self, build_playlist=True):
		self.conf = readConf()
		self.play_type = self.conf['play_type']
		self.play_needed = False
		log(f"nplayer.init():play_needed set = False", 'info')
		self.scale_needed = 0
		self.play_mode = 'database'
		if build_playlist:
			try:
				self.playlist = self.get_playlist_object(play_mode=self.play_mode, play_type=self.play_type)
			except Exception as e:
				log(f"db_playlist.init():Database contains no data! Running setup...", 'error')
				run_setup()
				log(f"db_playlist.init():Setup finished!", 'info')
				self.playlist = self.get_playlist_object(play_mode=self.play_mode, play_type=self.play_type)
		else:
			self.playlist = []
		self.next = None
		self.ART_UPDATE_NEEDED = False
		self.vlcInstance = None
		self.selected_playlist_item = None
		self.playlist_loop_one = False
		self.playlist_loop_all = True
		self.shuffle = False
		self.exit = False
		self.intro_start = None
		self.intro_end = None
		#self.continuous = 1
		#self.is_playing = 0
		self.continuous = True
		self.is_playing = False
		self.series_history = None
		self.resume = None
		self.play_pos = self.conf['nowplaying']['play_pos']
		self.viewer_win_w = 0
		self.viewer_win_h = 0
		self.viewer_win_scale = 0
		#self.version = 1.0
		#self.update_needed = False
		self.img_url = None
		self.POSTER = os.path.join(os.path.expanduser("~"), '.np', 'poster.png')
		self.POSTER_JPG = os.path.join(os.path.expanduser("~"), '.np', 'poster.jpg')
		self.gui_visible = False
		self.mfps = 0
		self.debug = self.conf['debug']
		self.is_paused = False
		self.wait_time = 2

	def get_playlist_object(self, data=None, play_mode=None, play_type=None, shuffle=False):
		#play type can be list: ['series', 'movies', etc]
		if play_type is not None:
			self.play_type = play_type
		if play_mode is not None:
			self.play_mode = play_mode
		if data is None:
			if not shuffle:
				if self.play_type == 'music' or self.play_type == 'movies' or self.play_type == 'videos':
					shuffle = True
				elif self.play_type == 'series':
					shuffle = False
			else:
				pass
			self.playlist = build_playlist(play_mode=self.play_mode, tables=self.play_type, shuffle=shuffle, new=False, save=True)
		else:
			self.playlist = build_playlist(play_mode=self.play_mode, tables=self.play_type, items=data, save=True)
		log(f"nplayer.get_playlist_object():Playlist created: play_type={self.play_type}, play_mode={self.play_mode}", 'info')
		return self.playlist

	def get_position(self):
		return self.player.get_position()

	def seek_to_pos(self, pos):
		self.pos = pos / 60
		try:
			self.player.set_position(self.pos)
			return self.pos
		except Exception as e:
			log("seek_to_pos, line 236: {e}", 'error')
			return 1

	def get_play_time(self):
		self.duration = self.player.get_time()
		return self.duration

	
	def get_mspf(self):
		self.mspf = int(1000 / (self.player.get_fps() or 25))
		return self.mspf

	def get_ts(self):
		self.ts = self.player.get_time()
		return self.ts

	def set_ts(self, ts):
		self.player.set_time(ts)
		self.ts = self.get_ts()
		return self.ts

	def step_frame(self, direction='fwd'):
		if self.player.get_state() == 3:
			self.player.pause()
		self.ts = self.player.get_time()
		self.mfps = int(1000 / (self.player.get_fps() or 25))
		if direction == 'fwd':
			self.ts += self.mfps
			log(f"Skipped next frame! ({self.ts})", 'info')
		elif direction == 'rev':
			self.ts -= self.mfps
			log(f"Skipped previous frame! ({self.ts})", 'info')
		self.player.set_time(self.ts)
		if self.player.get_state() == 3:
			self.player.pause()


	def playback_started(self):
		#self.is_playing = 1
		self.is_playing = True
		#self.play_needed = 0
		self.play_needed = False

	def init_vlc(self, uri=None):
		try:
			opts = self.conf['vlc']['opts']
		except:
			opts = '--no-xlib --audio-filter=normvol --norm-buff-size=20 --norm-max-level=2'
		self.vlcInstance = vlc.Instance(opts)
		log(f"nplayer.py, init_vlc(): Instance created! Options: {opts}", 'info')
		if uri == None:
			self.player = self.vlcInstance.media_player_new()
		else:
			self.player = self.vlcInstance.media_player_new(uri)
		self.player.audio_set_mute(self.conf['mute'])
		if self.conf['mute'] == False:
			self.player.audio_set_volume(self.conf['volume'])
		for evt in ['260:EventType.MediaMPPlaying', '261:EventType.MediaMPPaused', '262:EventType.MediaMPStopped', '265:EventType.MediaMPEndReached']:
			evid = int(evt.split(':')[0])
			event = vlc.EventType(evid)
			self.player.event_manager().event_attach(event, self.vlc_event)
		return self.player

	def playback_finished(self):
		log(f"nplayer.playback_finished():Playback ended!", 'info')
		self.conf['nowplaying']['filepath'] = None
		self.conf['nowplaying']['play_pos'] = 0
		writeConf(self.conf)

	def vlc_event(self, event):
		typestr = (str(event.type) + ":")
		self.is_playing = bool(self.player.is_playing())
		for event in ['260:EventType.MediaMPPlaying', '261:EventType.MediaMPPaused', '262:EventType.MediaMPStopped', '265:EventType.MediaMPEndReached']:
			if typestr in event:
				event = event.split(':')[1]
				if event == 'EventType.MediaMPEndReached':
					if not self.player.is_playing():
						self.play_needed = True
						log(f"nplayer.playback_finished():play_needed set = True (is_playing={self.is_playing})", 'info')
						self.playback_finished()
					else:
						#self.play_needed = False
						log(f"nplayer.playback_finished():skipping set play_needed (is_playing={self.is_playing}, late return for EventType.MediaMPEndReached!)", 'warning')
				elif event == 'EventType.MediaMPStopped':
					#self.is_playing = 0
					self.is_playing = False
				elif event == 'EventType.MediaMPPaused':
					self.is_paused = True
				elif event == 'EventType.MediaMPPlaying':
					self.is_paused = False
					#self.is_playing = self.player.is_playing()
					self.is_playing = bool(self.player.is_playing())
					#self.play_needed = 0
					#self.scale_needed = 1
					self.play_needed = False
					self.scale_needed = True
					log(f"play_needed set = 0 (vlc_event[MediaMPPlaying]", 'info')

	def get_next(self):
		self.next = self.playlist.next()
		return self.next

	def skip_next(self, shuffle=False):
		self.playlist.shuffle = shuffle
		log("nplayer.skip_next():Entered...", 'debug')
		self.next = self.playlist.next()
		log(f"nplayer.skip_next:Next set:{self.next}", 'info')
		self.play(self.next)
		log("nplayer.skip_next():Exited!", 'debug')

	def stop(self):
		self.player.stop()
		log("Playback stopped!", 'info')
		self.vlcInstance.release()
		log("VLC Instance released!", 'info')
		#self.is_playing = 0
		#self.continuous = 0
		#self.play_needed = 0
		self.is_playing = False
		self.continuous = False
		self.play_needed = False
		log(f"play_needed set = 0 (stop): line361", 'info')
		self.conf['nowplaying']['filepath'] = None

	def skip_previous(self):
		self.next = self.playlist.previous()
		log(f"nplayer.py:Skipped Previous!", 'info')
		self.play(self.next)

	def volume_set(self, vol):
		try:
			vol = int(vol)
			if vol <= 90:
				vol = vol + 10
			elif vol == 100 or vol >= 90:
				vol = 100
				log("Volume at max!", 'info')
			self.player.audio_set_volume(vol)
			self.conf['volume'] = vol
			return True
		except Exception as e:
			log(f"Error: Bad volume! Bad! Details: {e}", 'error')
			return False

	def volume_up(self):
		vol = int(self.conf['volume'])
		if vol <= 90:
			vol = vol + 10
		elif vol == 100 or vol >= 90:
			vol = 100
			log("Volume at max!", 'info')
		self.player.audio_set_volume(vol)
		self.conf['volume'] = vol

	def volume_down(self):
		vol = int(self.conf['volume'])
		if vol >= 0:
			vol = vol - 10
		elif vol == 0 or vol <= 10:
			vol = 0
			log("Volume at zero!", 'info')
		self.player.audio_set_volume(vol)
		self.conf['volume'] = vol

	def seek_fwd(self):
		pos = self.player.get_position()
		if pos >= 0.992:
			pos = 0.99
		pos = pos + 0.007
		self.player.set_position(pos)
		self.play_pos = pos
		log(f"nplayer.seek_fwd():Seeked to pos {self.play_pos}", 'info')
	
	def seek_rev(self):
		pos = self.player.get_position()
		if pos <= 0.008:
			pos = 0.0
		pos = pos - 0.007
		self.player.set_position(pos)
		self.play_pos = pos
		log(f"nplayer.seek_rev():Seeked to pos {self.play_pos}", 'info')

	def screenshot(self, src=0, dest_dir=None, w=0, h=0):
		ts = time.time()
		if dest_dir == None:
			dest_dir = os.path.join(os.path.expanduser("~"), 'Pictures', 'nplayer_caps', f"cap.{ts}.png")
		try:
			if self.conf['debug'] == True:
				log(f"snapshot: out_dir:{dest_dir}, w:{w}, h:{h}", 'info')
			ret = self.player.video_take_snapshot(src, dest_dir, w, h)
			if ret:
				log(f"nplayer snapshot return:{ret}", 'info')
				return True
		except Exception as e:
			log(f"failed to take snapshot:{e}", 'error')
			return False

	def constrain_scale(self, scale):
		if scale >= 10:
			return float(scale / 100)#Convert to 1-10 float value if in percentage
		else:
			return float(scale)#force to float if already in 1-10 scale

	def set_scale(self, filepath=None):
		try:
			if filepath == None:
				filepath = self.next
				log(f"nplayer.set_scale(): Filepath not provided, using self.next ({self.next}).", 'info')
			else:
				log(f"nplayer.set_scale(): Filepath provided: {filepath}", 'info')
			log(f"Getting prescale ratio...", 'info')
			prescale = self.player.video_get_scale()
			log(f"Prescale={prescale}", 'info')
			#self.viewer_win_scale = self.get_scaling()
			w, h = self.viewer_win_w, self.viewer_win_h
			log(f"calculating scale...", 'info')
			s = calculate_scale(filepath)
			log(f"scale calculated: {s}", 'info')
			scale = self.constrain_scale(s)
			self.player.video_set_scale(scale)
			#log(f"nplayer.set_scale(): Scale set! scale={scale}, prescale={prescale}", 'info')
			if prescale != scale:
				log(f"prescale and scale don't match! Details: prescale={prescale} ({type(prescale)}), scale={scale} ({type(scale)})", 'error')
				#self.scale_needed = 1
				#log(f"nplayer.set_scale():setting scale_needed=1.  Previous:{prescale}, Set:{scale}", 'info')
			elif prescale == scale:
				log(f"Scales match, skipping scale_needed. Previous:{prescale}, New:{scale}", 'info')
			self.scale_needed = 1
			self.scale = scale
			#log(f"nplayer.set_scale(): Scale set: {self.scale}", 'info')
		except Exception as e:
			log("nplayer.set_scale(): Unable to set scale: {e}", 'error')
			self.scale = 0
			self.scale_needed = 1

	def dl_img(self, filepath=None):
		if filepath is None:
			filepath = self.next
		test='https://www.google.com/imgres?imgurl='
		s = '&amp;imgrefurl'
		song = tag().read(filepath)
		print(song)
		if not song:
			return
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
		if self.img_url is not None:
			try:
				com = (f"wget --output-document 'poster.jpg' '{self.img_url}'")
				subprocess.check_output(com, shell=True)
			except Exception as e:
				log(f"Unable to get poster: {e}", 'error')
				return None
		else:
			return None
		screen = self.conf['screen']
		self.art_w = self.conf['windows'][screen]['viewer']['w']
		self.art_h = self.conf['windows'][screen]['viewer']['h']
		com = f"convert \"poster.jpg\" -resize {self.art_w}x{self.art_h} \"{self.POSTER}\""
		try:
			ret = subprocess.check_output(com, shell=True)
			self.album_art = self.POSTER
			return self.album_art
		except:
			return None


	def load_playlist(self, filepath):
		if self.conf['network']['media']['mode'] == 'remote':
			fpath = filepath.split('/var/storage/')[1]
			filepath = (os.path.expanduser("~"), '.np', 'sftp', fpath)
		if os.path.exists(filepath):
			try:
				results = []
				with open(filepath, 'r') as f:
					lines = f.read().strip().split("\n")
				f.close()
				if self.shuffle:
					shuffle(lines)
				return lines
			except Exception as e:
				log(f"Unable to load media playlist:{e}, {filepath}", 'error')
				return None
		else:
			log("Playlist file does not exist! '{filepath}'", 'error')
			return None


	def save_playlist(self, filepath, media_list=None):
		if media_list:
			if type(media_list) != list:
				media_list = media_list.playlist
		else:
			media_list = self.playlist.playlist
		print(media_list)
		l = []
		if len(media_list[0].split(':')) >= 3:
			for string in media_list:
				_id = string.split(':')[len(string.split(':')) - 1]
				play_type = string.split(':')[0]
				path = sqlite3(f"select filepath from {play_type} where id = {_id}")
				for line in path:
					l.append(line)
		if len(l) > 0:
			media_list = sorted(l)
		try:
			j = "\n"
			data = j.join(media_list)
			with open(filepath, 'w') as f:
				f.write(data)
			f.close()
			return True
		except Exception as e:
			log(f"Unable to save media playlist:{e}, {filepath}, {media_list}", 'error')
			return False

	def load_directory(self, path):
		try:
			com = (f"mkmedialist '{path}'")
			ret = subprocess.check_output(com, shell=True).decode().strip()
			if ret:
				log(f"Error: {ret}", 'error')
			playlist_file = os.path.join(path, 'medialist.txt')
			items = self.load_playlist(playlist_file)
			return items
		except Exception as e:
			log(f"Unable to load directory:({e}), {path}", 'error')
			return None

	def mount_sftp(self):
		com = f"sudo sshfs -o allow_other monkey@192.168.1.2:/var/storage /home/monkey/.np/sftp"
		try:
			ret = subprocess.check_output(com, shell=True).decode().strip()
			if ret != '':
				print(ret)
		except Exception as e:
			log(f"error running mount sftp (sshfs):{e}", 'error')


	def get_playlist_next(self):
		self.play_mode = 'playlist'
		for item in self.playlist.playlist:
			if '.part.' in item:
				log(f"Partial download encountered! Removing...", 'warning')
				self.playlist.playlist.remove(item)
		if self.playlist.current == None:
			self.next = self.playlist.next()
		else:
			if self.playlist_loop_one == True:
				self.next = self.playlist.current
			else:
				self.next = self.playlist.next()
		return self.next

	def play(self, filepath=None):
		self.series_history = read_history()
		self.next = None # init next to None for checks later.
		#if filepath provided...
		if filepath is not None:
			self.next = filepath
			log(f"nplayer.play():File provided: {self.next}. Set as next...", 'info')
		#else if resume from file...
		elif filepath is None and self.conf['nowplaying']['filepath'] is not None:
			if self.conf['nowplaying']['play_pos'] is not None:
				self.play_pos = self.conf['nowplaying']['play_pos']
				log(f"nplayer.play():play_pos set from conf (nowplaying): {self.play_pos}!", 'info')
			else:
				self.play_pos = 0
				log(f"nplayer.play():play_pos is None in conf! Setting 0...", 'info')
			self.next = self.conf['nowplaying']['filepath']
			log(f"Resuming from file (nowplaying): {self.next}. Set as next...", 'info')
		#if next is set, check if remains of playlist mode in next string...
		if self.next is not None:
			if is_npstring(self.next):
				log(f"nplayer.play():Converting next from npstring ({self.next})...", 'info')
				self.next = path_from_npstring(self.next)
			try:
				self.play_type = test_media(self.next)
				log(f"nplayer.play():Play Type set (from test_media()): {self.play_type}", 'info')
			except:
				log(f"nplayer.play():test_media failed! Setting 'videos'...", 'info')
				self.play_type = 'videos'
		# if next is not set...
		else:
			#if mode is  playlist
			if self.play_mode == 'playlist':
				log(f"nplayer.play():Playlist mode, getting next...", 'info')
				self.next = self.get_playlist_next()
				self.play_pos = 0
				log(f"nplayer.play():Playlist mode, next={self.next}, pos={self.play_pos}", 'info')
			elif self.play_mode == 'database':
				self.next = self.get_next()
				self.play_pos = 0
				log(f"Database: Getting next:{self.next}", 'info')
		#By this point, next should be set.
		if self.play_mode == 'playlist':
			if self.play_type == 'series':
				try:
					query_string = ("filepath like '%" + self.next + "%'")
					series_name = querydb('series', 'series_name', query_string)[0][0]
					self.series_history[series_name] = self.next
					write_history(self.series_history)
				except Exception as e:
					log(f"Couldn't find series db or history...(playlist?)", 'warning')
					pass
		elif self.play_mode == 'database':
			series_name = None		
			if self.play_type == 'series':
				try:
					query_string = ("filepath like '%" + self.next + "%'")
					log(f"Query string: {query_string}", 'info')
					series_name = querydb('series', 'series_name', query_string)[0][0]
					self.series_history[series_name] = self.next
					write_history(self.series_history)
				except Exception as e:
					log(f"Series query failed: (not series type?) {e}", 'warning')
					pass
		#Guess intro
		intro = guess_intro(self.next)
		if intro is not None:
			self.conf['intro'] = {}
			self.conf['intro']['start'] = intro[0]
			self.conf['intro']['end'] = intro[1]
			log(f"Intro detected! Start={intro[0]}, End={intro[1]}", 'info')
		else:
			self.conf['intro'] = {}
			self.conf['intro']['start'] = None
			self.conf['intro']['end'] = None
			log(f"No intro found for '{self.next}'", 'info')
		# check for vlc instance
		if self.vlcInstance is None:
			try:
				opts = self.conf['vlc']['opts']
				log(f"nplayer.play():VLC cli options loaded from conf.", 'info')
			except Exception as e:
				log(f"nplayer.play():Couldn't load options from conf! ({e})", 'error')
				opts = "--no-xlib"
			self.vlcInstance = vlc.Instance(opts)
			log(f"nplayer.py, play(): Instance created! Options: {opts}", 'info')
			self.player = self.vlcInstance.media_player_new()
			log(f"nplayer.play():player object created!", 'info')
		# check if network mode is remote:
		if self.conf['network']['media']['mode'] == 'remote':
			if '/.np/sftp' not in self.next:
				if self.conf['media_directories']['main'] in self.next:
					fpath = self.next.split(self.conf['media_directories']['main'])[1]
					homedir = os.path.expanduser("~")
					self.next = f"{homedir}{os.path.sep}.np{os.path.sep}sftp{os.path.sep}fpath"
					log(f"Network uri set:{self.next}", 'info')
				else:
					log(f"bad string: next:{self.next}, media_dirs:{self.conf['media_directories']['main']}", 'error')
					if '/var/storage' in self.next:
						fpath = self.next.split('/var/storage')[1]
						homedir = os.path.expanduser("~")
						self.next = f"{homedir}{os.path.sep}.np{os.path.sep}sftp{os.path.sep}fpath"
					else:
						log(f"Couldn't parse network path! '/var/storage' not in path!", 'error')
		# attempt to set media path.
		try:
			log(f"nplayer.play(): Setting media path:{self.next}", 'info')
			self.player.set_media(self.vlcInstance.media_new_path(self.next))
			log(f"nplayer.play(): Starting playback...", 'info')
			self.player.play()
			log(f"nplayer.play(): Waiting {self.wait_time} seconds before scale...", 'info')
			time.sleep(self.wait_time) # wait for media to load to aid scaling method
		except Exception as e:
			log(f"Unable to open media item:{e}, filepath={self.next}", 'error')
			if self.conf['network']['media']['mode'] == 'remote':
				self.mount_sftp()
				self.player.set_media(self.vlcInstance.media_new_path(self.next))
				self.player.play()
				self.is_url = False
		# set play position if greater than 0
		if self.play_pos > 0:
			self.player.set_position(self.play_pos)
			log(f"nplayer.play(): Skipped to position {self.play_pos}", 'info')
			#set play_needed and play_pos to False to avoid loop duplicating action (delay?)
			self.play_needed = False
			log(f"nplayer.play(): play_needed set False!", 'info')
			self.play_pos = 0
			log(f"nplayer.play(): play_pos set to 0!", 'info')
			self.conf['nowplaying']['play_pos'] = 0
		self.continuous = True
		if self.play_type == 'series' or  self.play_type == 'movies':
			if self.next is not None:
				try:
					self.set_scale(self.next)
					log("nplayer.play(): set scale exited!", 'info')
				except Exception as e:
					log(f"nplayer.play(): Couldn't set scale! {e}", 'error')
					self.scale_needed = 1
			else:
				log(f"WARNING:next not set! {self.next}. Retrying...", 'warning')
				self.next == self.get_next()
				try:
					#log("nplayer.play(): set scale started!", 'info')
					self.set_scale(self.next)
					#log("nplayer.play(): set scale exited!", 'info')
				except Exception as e:
					log(f"nplayer.play(): Couldn't set scale! {e}", 'error')
					self.scale_needed = 1
		#set volume
		try:
			self.volume = self.player.audio_get_volume()
			log(f"nplayer.play(): Retreived volume({self.volume})", 'info')
		except Exception as e:
			log(f"Unable to set volume: {e}", 'error')
		self.is_playing = self.player.is_playing()
		log(f"nplayer.py.play(): is_playing set: {self.is_playing}", 'info')
		if self.is_playing:
			self.conf['nowplaying']['filepath'] = self.next
			self.conf['nowplaying']['play_pos'] = self.play_pos
			self.play_needed = False
			self.mfps = self.get_mspf()
			log(f"nplayer.play():Playback started ({self.next})! Setting play needed=False", 'info')
		if self.play_type == 'music':
			try:
				self.album_art = self.dl_img()
				self.ART_UPDATE_NEEDED = True
				log(f"nplayer.py.play(): ART_UPDATE_NEEDED set (True)", 'info')
			except Exception as e:
				log(f"nplayer.play:unable to get art! ({e})", 'error')
				self.album_art = None
				self.ART_UPDATE_NEEDED = False
		elif self.play_type == 'movies' or self.play_type == 'series':
			self.ART_UPDATE_NEEDED = True
			log(f"nplayer.play:Art update needed flag set! (True)", 'info')
		writeConf(self.conf)
		log(f"nplayer.play(): Exited! (play_needed={self.play_needed}), object={self}", 'info')
