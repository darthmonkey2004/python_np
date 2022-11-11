import subprocess
import os
from PIL import Image
import requests
import subprocess
from urllib.parse import quote, unquote
import np
import vlc
import time
from np.utils.playlist import get_next
from np.core.log import np_logger
import PySimpleGUI as sg
from np.core.playlist import playlist, db_playlist
from random import shuffle

log = np_logger().log_msg


def sqlite3(com):
	path = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	com = f"sqlite3 \"{path}\" \"{com}\""
	return subprocess.check_output(com, shell=True).decode().strip().split("\n")

#-------------main player class=------------#
class nplayer():
	def __init__(self):
		self.is_url = False
		self.conf = {}
		self.conf['vlc'] = {}
		try:
			self.conf = np.readConf()
		except Exception as e:
			log(f"Exception reading conf file: will wipe the stored window locations... {e}", 'warning')
			self.conf = np.initConf()
			self.conf['windows'] = np.init_window_position()
		self.conf['grab_devices'] = ['/dev/input/event11']
		self.play_type = self.conf['play_type']
		self.history_pos = 0
		self.history = {}
		self.history['history'] = []
		self.history['pos'] = len(self.history['history']) - 1
		self.history['playing_from_history'] = False
		self.series_history = None
		self.play_needed = 1
		log(f"nplayer.init():play_needed set = 1", 'info')
		self.scale_needed = 0
		self.playlist = db_playlist(np.create_media(self.play_type))
		self.dbmgr_picked_items = []
		self.next = None
		self.ART_UPDATE_NEEDED = False
		self.vlcInstance = None
		self.selected_playlist_item = None
		self.play_mode = 'database'
		self.playlist_last = None
		self.playlist_loop_one = False
		self.playlist_loop_all = True
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
		self.viewer_win_w = 0
		self.viewer_win_h = 0
		self.viewer_win_scale = 0
		self.version = 1.0
		self.update_needed = False
		self.shuffle = True
		

	def get_playlist_object(self, data=None, mode=None):
		if mode is not None:
			self.play_mode = mode
		if data is None:
			if self.play_mode == 'database':
				self.playlist = db_playlist()
			else:
				self.playlist = playlist()
		else:
			if self.play_mode == 'database':
				self.playlist = db_playlist(data)
			else:
				self.playlist = playlist(data)
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


	def playback_started(self):
		self.is_playing = 1
		self.play_needed = 0


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
		self.conf['nowplaying']['filepath'] = None
		np.writeConf(self.conf)
		self.play_needed = 1
		log(f"nplayer.playback_finished():play_needed set = 1", 'info')


	def vlc_event(self, event):
		typestr = (str(event.type) + ":")
		for event in ['260:EventType.MediaMPPlaying', '261:EventType.MediaMPPaused', '262:EventType.MediaMPStopped', '265:EventType.MediaMPEndReached']:
			if typestr in event:
				event = event.split(':')[1]
				if event == 'EventType.MediaMPEndReached':
					self.play_needed = 1
					log(f"nplayer.vlc_event():play_needed set = 1 (vlc_event[MediaMPEndReached])", 'info')
					self.playback_finished()
				elif event == 'EventType.MediaMPStopped':
					self.is_playing = 0
				elif event == 'EventType.MediaMPPaused':
					pass
				elif event == 'EventType.MediaMPPlaying':
					self.is_playing = self.player.is_playing()
					self.play_needed = 0
					self.scale_needed = 1
					log(f"play_needed set = 0 (vlc_event[MediaMPPlaying]", 'info')

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

	def get_next_series_name(self):
		query = f"select distinct series_name from series;"
		series = sqlite3(query)
		if self.shuffle:
			shuffle(series)
			shuffle(series)
			shuffle(series)
		return series[0]


	def get_next_movie(self):
		query = f"select distinct filepath from movies order by title;"
		movies = sqlite3(query)
		if self.shuffle:
			shuffle(movies)
			shuffle(movies)
			shuffle(movies)
		return movies[0]

			
	def get_next(self):
		if self.play_mode == 'database':
			if self.play_type == 'series':
				series_name = self.get_next_series_name()
				self.series_history = np.read_history()
				last = self.series_history[series_name]
				files = sqlite3(f"select filepath from {self.play_type} where series_name like \'%{series_name}%\' order by season,episode_number;")
				idx = files.index(last) + 1
				try:
					self.next = files[idx]
				except Exception as e:
					log(f"nplayer.get_next():Reached end of series! Starting over...({e})", 'info')
					self.next = files[0]
			elif self.play_type == 'movies':
				self.next = self.get_next_movie()
			elif self.play_type == 'music':
				if self.shuffle:
					shuffle(self.playlist.playlist)
					shuffle(self.playlist.playlist)
					shuffle(self.playlist.playlist)
					self.next = self.playlist.playlist[0]
				else:
					self.next = self.playlist.next()
		else:
			self.next = self.playlist.next()
		return self.next


	def skip_next(self):
		self.next = self.get_next()
		log(f"Skipped next!", 'info')
		self.play(self.next)


	def stop(self):
		self.player.stop()
		log("Playback stopped!", 'info')
		self.vlcInstance.release()
		log("VLC Instance released!", 'info')
		self.is_playing = 0
		self.continuous = 0
		self.play_needed = 0
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
		
		
	def seek_rev(self):
		pos = self.player.get_position()
		if pos <= 0.008:
			pos = 0.0
		pos = pos - 0.007
		self.player.set_position(pos)

	
	def screenshot(self, src=0, dest_dir=None, w=0, h=0):
		ts = time.time()
		if dest_dir == None:
			dest_dir = os.path.join(os.path.expanduser("~"), '.np', f"cap.{ts}.png")
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
			s = np.calculate_scale(filepath)
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

						

	def play(self, _file=None):
		if self.next is not None:
			self.playlist_last = self.next
		print(self.play_mode)
		self.resume = None
		self.series_history = np.read_history()
		self.next = None
		#if filepath provided...
		if _file is not None:
			self.next = _file
			log(f"File provided: {self.next}. Set as next...", 'info')
		#else if resume from file...
		elif _file is None and self.conf['nowplaying']['filepath'] is not None:
			if self.conf['nowplaying']['play_pos'] is not None:
				self.play_pos = self.conf['nowplaying']['play_pos']
			else:
				self.play_pos = 0
			self.next = self.conf['nowplaying']['filepath']
			log(f"Resuming from file (nowplaying): {self.next}. Set as next...", 'info')
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
				log("TODO: check playlist item string and parse out filepath!", 'info')
			#test type vs file string
			self.play_type = self.play_type
			if self.play_type == 'series' or self.play_type == 'movies':
				if self.conf['media_directories']['music'] in self.next:
					self.next = None
					log("Stale type found as filepath. Setting as None...", 'warning')
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
			self.selected_playlist_item = self.get_info_string(self.next)
			l = len(list(self.history.values()))
			self.history[l] = self.playlist_last
			if self.conf['debug'] == True:
				log(f"playlist last set in MP.play(): playlist_last:{self.playlist_last}, play_mode={self.play_mode}", 'info')
			if self.play_type == 'series':
				try:
					query_string = ("filepath like '%" + self.next + "%'")
					series_name = np.querydb('series', 'series_name', query_string)[0][0]
					self.series_history[series_name] = self.next
					np.write_history(self.series_history)
				except Exception as e:
					log(f"Couldn't find series db or history...(playlist?)", 'warning')
					pass

		elif self.play_mode == 'database':
			series_name = None		
			if self.play_type == 'series':
				try:
					query_string = ("filepath like '%" + self.next + "%'")
					log(f"Query string: {query_string}", 'info')
					series_name = np.querydb('series', 'series_name', query_string)[0][0]
					self.series_history[series_name] = self.next
					np.write_history(self.series_history)
				except Exception as e:
					log(f"Series query failed: (not series type?) {e}", 'warning')
					pass

		#Guess intro
		intro = np.guess_intro(self.next)
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
			except:
				opts = "--no-xlib"
			self.vlcInstance = vlc.Instance(opts)
			log(f"nplayer.py, play(): Instance created! Options: {opts}", 'info')
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
				self.next = (os.path.expanduser("~"), '.np', 'sftp', fpath)
				log(f"Network uri set:{self.next}", 'info')
		# attempt to set media path.
		try:
			log(f"nplayer.py.play(): Setting media path:{self.next}", 'info')
			self.player.set_media(self.vlcInstance.media_new_path(self.next))
			log(f"nplayer.py.play(): Starting playback...", 'info')
			self.player.play()
			#log(f"nplayer.play(): Waiting 2 secs...is_playing={self.player.is_playing()}", 'info')
			time.sleep(2)
			#log(f"nplayer.play(): Wait over.", 'info')
			self.is_url = False
		except Exception as e:
			log(f"Unable to open media item:{e}, filepath={self.next}", 'error')
			if self.conf['network_mode']['media_mode'] == 'remote':
				self.mount_sftp()
				self.player.set_media(self.vlcInstance.media_new_path(self.next))
				self.player.play()
				self.is_url = False
		# set play position if greater than 0
		if self.play_pos > 0:
			self.player.set_position(self.play_pos)
			log(f"nplayer.play(): Skipped to position {self.play_pos}", 'info')
			#set play_needed and play_pos to 0 to avoid loop duplicating action (delay?)
			self.play_needed = 0
			self.play_pos = 0
			self.conf['nowplaying']['play_pos'] = 0
		self.continuous = 1
		if self.play_type == 'series' or  self.play_type == 'movies':
			if self.is_url == False:
				if self.next is not None:
					try:
						#log("nplayer.play(): set scale started!", 'info')
						self.set_scale(self.next)
						#log("nplayer.play(): set scale exited!", 'info')
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
		if self.is_playing == 1 or self.is_playing == True:
			self.conf['nowplaying']['filepath'] = self.next
			self.conf['nowplaying']['play_pos'] = self.play_pos
			self.play_needed = 0
			log(f"nplayer.play():Playback started ({self.next})! Setting play needed=0", 'info')
		else:
			log(f"nplayer.play():set play_needed = 1, not started!(???) next={self.next}, is_playing={self.player.is_playing()}", 'error')
			self.play_needed = 1

		if self.play_type == 'music':
			try:
				self.album_art = self.dl_img()
				self.ART_UPDATE_NEEDED = True
			except Exception as e:
				log(f"nplayer.play:unable to get art! ({e})", 'error')
				self.ART_UPDATE_NEEDED = False
		np.writeConf(self.conf)
		log(f"nplayer.play(): Exited! (play_needed={self.play_needed}), object={self}", 'info')


	def dl_img(self, filepath=None):
		if filepath is None:
			filepath = self.next
		test='https://www.google.com/imgres?imgurl='
		s = '&amp;imgrefurl'
		song = np.tag().read(filepath)
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
		try:
			com = ("wget --output-document 'poster.jpg' '" + self.img_url + "'")
			subprocess.check_output(com, shell=True)
		except Exception as e:
			log(f"Unable to get poster: {e}", 'error')
		screen = self.conf['screen']
		self.art_w = self.conf['windows'][screen]['viewer']['w']
		self.art_h = self.conf['windows'][screen]['viewer']['h']
		com = ("convert 'poster.jpg' -resize " + str(self.art_w) + "x" + str(self.art_h) + " 'poster.png'")
		try:
			ret = subprocess.check_output(com, shell=True)
			self.album_art = 'poster.png'
			return self.album_art
		except:
			return None


	def load_playlist(self, filepath):
		if self.conf['network_mode']['media_mode'] == 'remote':
			fpath = filepath.split('/var/storage/')[1]
			filepath = (os.path.expanduser("~"), '.np', 'sftp', fpath)
		if os.path.exists(filepath):
			try:
				results = []
				with open(filepath, 'r') as f:
					lines = f.read().strip().split("\n")
				f.close()
				return lines
			except Exception as e:
				log(f"Unable to load media playlist:{e}, {filepath}", 'error')
				return None
		else:
			log("Playlist file does not exist! '{filepath}'", 'error')
			return None


	def save_playlist(self, filepath, media_list=None):
		if media_list:
			media_list = media_list.playlist
		else:
			media_list = self.playlist.playlist
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



	
