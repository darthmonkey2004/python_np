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
		self.history_pos = 0
		self.history = {}
		self.history['history'] = []
		self.history['pos'] = len(self.history['history']) - 1
		self.history['playing_from_history'] = False
		self.series_history = None
		self.play_needed = 1
		log(f"nplayer.init():play_needed set = 1", 'info')
		self.scale_needed = 0
		self.playlist = np.create_media(self.conf['play_type'])
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
			
	def get_next(self):
		self.next = get_next()
		return self.next


	def history_next_pos(self):
		old_pos = self.history['pos']
		self.history['pos'] = self.history['pos'] + 1
		if self.history['pos'] == len(self.history['history']):
			log("Reached end of history, disabing playing from history flag", 'info')
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
			log("Reached beginning of history, resetting position to 0", 'info')
			self.history['pos'] = 0
		return self.history['pos']

	def skip_next(self):
		self.conf['nowplaying']['filepath'] = None
		self.conf['nowplaying']['play_pos'] = 0
		log(f"nplayer.py, skip_next: blanked nowplaying info (None, 0)", 'info')
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
				log(f"skip_next, Not using history:{self.history['history']}", 'info')
		elif self.history['playing_from_history'] == True:
			try:
				self.history['pos'] = self.history_next_pos()
				self.next = self.history['history'][self.history['pos']]
				
				log(f"skip_next: Using History at pos:{self.history_pos}, {self.next}", 'info')
				self.play(self.next)
			except Exception as e:
				log(f"line 230: Reached end of playback history. Getting next from media list:{e}", 'info')
				self.history['playing_from_history'] = False
				self.history['pos'] = len(self.history['history']) - 1
				log(f"Reset history pos:{self.history['pos']}, {len(self.history['history'])}", 'info')
				self.stop()
				self.next = self.get_next()
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
		self.history['playing_from_history'] = True
		log(f"old history pos:Position={self.history['pos']}, Length={len(self.history['history'])}", 'info')
		self.history['pos'] = self.history_prev_pos(self.history['pos'])
		log(f"new history pos:Position={self.history['pos']}, Length={len(self.history['history'])}", 'info')
		try:
			self.next = self.history['history'][self.history['pos']]
			log(f"self.next set from history index({self.history['pos']}):{self.next}", 'info')
		except Exception as e:
			self.next = self.playlist[self.history['pos']]
			log(f"Error setting next from history: {e}, next='{self.next}'", 'error')
		
		if 'series:' in self.next:
			_id = self.next.split(':')[5]
			qstring = ("id = '" + _id + "'")
			self.next = np.querydb(table='series', column='filepath', query=qstring)[0][0]
		elif 'movies:' in self.next:
			_id = self.next.split(':')[3]
			qstring = ("id = '" + _id + "'")
			self.next = np.querydb(table='movies', column='filepath', query=qstring)[0][0]
		elif 'music:' in self.next:
			log("TODO: check playlist item string and parse out filepath!")
		log("Previous:" + self.next)
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



	#def get_scaling(self):
	#	# called before window created
	#	root = sg.tk.Tk()
	#	self.viewer_win_scale = root.winfo_fpixels('1i')/72
	#	root.destroy()
	#	return self.viewer_win_scale



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
			self.scale_needed = 0
			self.scale = scale
			#log(f"nplayer.set_scale(): Scale set: {self.scale}", 'info')
		except Exception as e:
			log("nplayer.set_scale(): Unable to set scale: {e}", 'error')
			self.scale = 0
			self.scale_needed = 1

						

	def play(self, _file=None):
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
			play_type = self.conf['play_type']
			if play_type == 'series' or play_type == 'movies':
				if self.conf['media_directories']['music'] in self.next:
					self.next = None
					log("Stale type found as filepath. Setting as None...", 'warning')
		# if next is not set...
		if self.next is None:
			#if mode is  playlist
			if self.play_mode == 'playlist':
				self.next = self.get_playlist_next()
				self.play_pos = 0
				log(f"Playlist: Getting next:{self.next}", 'info')
			elif self.play_mode == 'database':
				self.next = self.get_next()
				self.play_pos = 0
				log(f"Database: Getting next:{self.next}", 'info')
		#By this point, next should be set.
		if self.play_mode == 'playlist':
			self.playlist_last = self.next
			self.selected_playlist_item = self.get_info_string(self.next)
			l = len(list(self.history.values()))
			self.history[l] = self.playlist_last
			if self.conf['debug'] == True:
				log(f"playlist last set in MP.play(): playlist_last:{self.playlist_last}, play_mode={self.play_mode}", 'info')
			if self.conf['play_type'] == 'series':
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
			if self.conf['play_type'] == 'series':
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
		if self.conf['play_type'] == 'series' or  self.conf['play_type'] == 'movies':
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

		if self.conf['play_type'] == 'music':
			self.album_art = self.dl_img()
			self.ART_UPDATE_NEEDED = True
		np.writeConf(self.conf)
		log(f"nplayer.play(): Exited! (play_needed={self.play_needed}), object={self}", 'info')


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


	def save_playlist(self, filepath, media_list):
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
			playlist = os.path.join(path, 'medialist.txt')
			items = self.load_playlist(playlist)
			return items
		except Exception as e:
			log(f"Unable to load directory:({e}), {path}", 'error')
			return None


	def build_info_string_from_filepath(self, filepath):
		try:
			log("running build info from filepath", 'info')
			qstring = ("filepath = '" + filepath + "'")
			try:
				series_name, season, episode_number, episode_name, _id = np.querydb('series', 'series_name,season,episode_number,episode_name,id', qstring)[0]
				sstring = (f"series:{series_name}:{season}:{episode_number}:{episode_name}:{_id}")
				log(f"Series string:{sstring}", 'info')
			except:
				sstring = None
			try:
				title, year, _id = np.querydb('movies', 'title,year,id', qstring)[0]
				mvstring = ("movies:" + title + ":" + str(year) + ":" + str(_id))
				log(f"Movies string:{mvstring}", 'info')
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
				log(f"data not found in database: {filepath}", 'info')
				return None
		except:
			log(f"data not found in database: {filepath}", 'info')


	def get_playlist_next(self):
		self.play_mode = 'playlist'
		items = self.playlist
		for item in items:
			if '.part.' in item:
				log(f"Partial download encountered! Removing...", 'warning')
				items.remove(item)
		log(f"PLAYLIST_ITEMS/items:{items}", 'info')
		idx = None
		if self.playlist_last is None:
			try:
				self.next = items[0]
				log(f"Playlist next set to 0: {self.next}", 'info')
			except Exception as e:
				log(f"Playlist appears empty!{e}", 'error')
				self.play_mode = 'database'
				return None
		else:
			if self.playlist_loop_one == True:
				self.next = self.playlist_last
				if self.conf['debug'] == True:
					log(f"Playlist next is playlist last, loop_one=True.", 'info')
				return self.next
			else:
				self.playlist_last = self.next
				log(f"self.playlist_last:{self.playlist_last}", 'debug')
				string = self.build_info_string_from_filepath(self.playlist_last)
				if self.conf['debug'] == True:
					log(f"Built playlist parse string from filepath. string={string}, filepath='{self.playlist_last}'", 'info')
				try:
					idx = items.index(string)
					log(f"Index set from string: {idx}, {string}", "info")
				except Exception as e:
					idx = 1
					log(f"Exception setting index with string {string}:{e}", 'error')
				query_string = (f"filepath = '{string}'")
				log(f"Query string:{query_string}", 'debug')
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
			log("TODO: check playlist item string and parse out filepath!", 'error')

		return self.next
	
