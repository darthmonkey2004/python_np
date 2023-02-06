from np.core.log import np_logger
from np.core.core import read_history, write_history
import pickle
from random import randint
from random import shuffle as random
from np.core.nplayer_db import querydb
import os
import subprocess
from np.core.conf import readConf, writeConf
log = np_logger().log_msg

conf = readConf()

def load_playlist_file(filepath):
	if conf['network_mode']['media_mode'] == 'remote':
		fpath = filepath.split('/var/storage/')[1]
		filepath = (os.path.expanduser("~"), '.np', 'sftp', fpath)
	if os.path.exists(filepath):
		results = []
		with open(filepath, 'r') as f:
			lines = f.read().strip().split("\n")
		f.close()
		return lines
	else:
		print("Playlist file does not exist! '{filepath}'")
		return None


def load_directory(path):
	try:
		com = (f"mkmedialist '{path}'")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			print(f"Error: {ret}")
		playlist_file = os.path.join(path, 'medialist.txt')
		items = load_playlist_file(playlist_file)
		return sorted(items)
	except Exception as e:
		print("Couldn't load directory:", e)
		return []



def create_temp_history():
	h = read_history()
	ret = write_temp_history(h)
	if not ret:
		txt = f"Failed to create temp history! result:{ret}"
		raise Exception(Exception, txt)
	else:
		return True

def rm_temp_history():
	tempfile = os.path.join(os.path.expanduser("~"), '.np', 'np.history.temp')
	ret = subprocess.check_output(f"rm \"{tempfile}\"", shell=True).decode().strip()
	if ret != '':
		msg = ret
		ret = False
	else:
		msg = None
		ret = True
	return ret, msg

def write_temp_history(history):
	try:
		tempfile = os.path.join(os.path.expanduser("~"), '.np', 'np.history.temp')
		with open(tempfile, 'wb') as f:
			pickle.dump(history, f)
			f.close()
		return True
	except Exception as e:
		print(f"playlist.write_temp_history():Error - {e}", 'error')
		return False
	
def read_temp_history():
	try:
		tempfile = os.path.join(os.path.expanduser("~"), '.np', 'np.history.temp')
		with open(tempfile, 'rb') as f:
			history = pickle.load(f)
			f.close()
		return history
	except Exception as e:
		print(f"playlist.read_temp_history():Error - {e}", 'error')
		return None

class db_playlist():
	def __init__(self, items=None, save=True, loop_one=False, loop_all=False, shuffle=False, play_type=None):
		if play_type is None:
			conf = readConf()
			self.play_type = conf['play_type']
		else:
			self.play_type = play_type
		self.playlist_min_ct = len(get_series_names())
		self.shuffle = shuffle
		self.last = []
		self.current = None
		self.loop_one = loop_one
		self.loop_all = loop_all
		self.save = save
		if items is not None:
			self.playlist = self.set(items)
		else:
			self.playlist = None

	def set(self, items):
		if isinstance(items, playlist) or isinstance(items, db_playlist):
			items = items.playlist
		elif items == str:
			items = items.splitlines()
		if type(items) == list:
			print("items:", len(items))
			self.playlist = items
		if self.shuffle:
			random(self.playlist)
		log(f"db_playlist.set():Playlist data set! ({len(self.playlist)})", 'info')
		return self


	def path_from_npstring(self, string):
		idx = string.split(':')[len(string.split(':')) - 1]
		table = string.split(':')[0]
		qstring = f"id = \'{idx}\'"
		return querydb(table=table, column='filepath', query=qstring)[0][0]


	def npstring_from_path(self, path):
		return npstring_from_path(path)

		
	def clear(self):
		self.playlist = []
		self.currnet = None
		log(f"playlist():playlist cleared!", 'info')
		return


	def next(self):
		if self.loop_one:
			#if repeat one, do nothing (leave current as current)
			pass
		else:
			#if not repeat one, pop from playlist and append to last
			last = self.playlist.pop(0)
			self.last.append(last)# and store in last list
			log(f"playlist.next():set last ({last})!", 'info')
		if self.loop_all:
			if len(self.playlist) == 0:
				#if playlist is empty and in repeat mode, set playlist to history
				self.playlist = self.last
				self.last = []
				log(f"Reset playlist items to last (loop_all=True)!", 'info')
		else:
			last = self.playlist.pop(0)
			self.last.append(last)# and store in last list
			if len(self.playlist) <= self.playlist_min_ct:
				#if minimum playlist items reached, execute build and append to current
				self.playlist = build_playlist(items=self.playlist)		
				#update current saved playlist in pickle dat file
		if self.save:
			log(f"Saving playlist (save is True)...")
			save_playlist(self.playlist)
		#if we haven't reached the end of playlist...
		if len(self.playlist) > 0:
			if not self.loop_one:
				# if not repeat one, set current to 0 (assuming pop earlier)
				self.current = self.playlist[0]
				log(f"playlist.next():set current ({self.current})!", 'info')
			else:
				self.current = self.current
				log(f"Repeating: {self.current} (loop_one=True)", 'info')
		else:
			#End of playlist shouldn't happen, as it rebuilds after length <= self.playlist_min_ct
			self.current = None
			log(f"Error: Playlist is empty! Populate playlist using .set(items) to use this!")
			return self.current#return Non
		if is_npstring(self.current):
			self.current = path_from_npstring(self.current)
		save_playlist(self.playlist)
		return self.current

	def previous(self):
		if self.current is None:
			if self.last == []:
				# if last is empty, log playlist restart, and set current to first in playlist
				log(f"Reached beginning of playlist!", 'info')
				self.current = self.playlist[0]
			else:
				#if last is set, grab last item index in last list
				item = self.last.pop(len(self.last) - 1)
				#create temporary list in reverse order so item is put to end...
				l = self.playlist.reverse()
				l.append(item)
				#reverse again, so added item at front
				self.playlist = l.reverse()
				self.current = item
		if self.current is None:
			log(f"playlist.previous():self.current returned None!", 'error')
			return None
		if is_npstring(self.current):
			self.current = path_from_npstring(self.current)
		return self.current


class playlist():
	def __init__(self, playlist_file=None, items=None, media_path=None, shuffle=False, loop_one=False, loop_all=False):
		self.playlist_file = playlist_file
		self.playlist = items
		self.media_path = media_path
		self.shuffle = shuffle
		self.loop_one = loop_one
		self.loop_all = loop_all
		self.last = []
		conf = readConf()
		self.network_mode = conf['network_mode']['media_mode']
		self.current = None
		if self.media_path is not None:
			self.playlist = self.load_directory(self.media_path)
			if self.shuffle:
				random(self.playlist)	
				#print("random, by directory", len(self.playlist))
			else:
				self.playlist = sorted(self.playlist)
		elif self.playlist_file is not None:
			self.playlist = subprocess.check_output(f"cat \"{self.playlist_file}\"", shell=True).decode().strip().split("\n")
			if self.shuffle:
				random(self.playlist)
			else:
				self.playlist = sorted(self.playlist)
		elif self.playlist is not None:
			log("No parent directory provided! Attempting to find common path...")
			try:
				self.media_path = self.find_parent_dir(self.playlist)
			except Exception as e:
				log(f"Won't be able to auto build playlist on end of playlist...", 'warning')
				self.media_path = None
			if self.shuffle:
				self.playlist = random(self.playlist)
			else:
				self.playlist = sorted(self.playlist)
		if self.media_path is not None:
			self.playlist_file = os.path.join(self.media_path, 'medialist.txt')

	def load_playlist_file(self, filepath=None):
		if filepath is not None:
			self.playlist_file = filepath
		if os.path.exists(self.playlist_file):
			with open(self.playlist_file, 'r') as f:
				lines = f.read().strip().split("\n")
			f.close()
			return lines
		else:
			log("Playlist file does not exist! '{self.playlist_file}'", 'error')
			return None


	def load_directory(self, path=None):
		if path is not None:
			self.media_path = path
		try:
			com = (f"mkmedialist '{self.media_path}'")
			ret = subprocess.check_output(com, shell=True).decode().strip()
			if ret:
				log(f"Error: {ret}")
			self.playlist_file = os.path.join(self.media_path, 'medialist.txt')
			self.playlist = self.load_playlist_file(self.playlist_file)
			return self.playlist
		except Exception as e:
			log(f"Couldn't load directory ({self.media_path}):{e}", 'error')
			return []


	def test_common_dir(self, t, items=None):
		if items is not None:
			self.playlist = items
		ct = len(self.playlist)
		string = "\n".join(self.playlist)
		if t in string:
			l = string.split(t)
			if l[0] == '':
				_ = l.pop(0)
			tct = len(l)
			print(ct, tct)
			if ct == tct:
				print("matched!", t)
				return True
			else:
				print("No match...", t)
				return False

	def find_parent_dir(self, items=None):
		if items is not None:
			self.playlist = items
		depth = len(self.playlist[0].split('/'))
		ct = len(self.playlist)
		#compares a list and determines common parent directory,
		# to serve as media_dir for playlist reconstruction
		#grab item for pathing
		pos = 1
		t1 = os.path.dirname(self.playlist[0])
		if self.test_common_dir(t1):
			#if test is true, return t1
			return t1
		else:
			pos += 1
		if pos <= depth:
			#if not true, continue with process
			t2 = os.path.dirname(t1)
			if self.test_common_dir(t2):
				return t2
			else:
				pos += 1
		if pos <= depth:
			t3 = os.path.dirname(t2)
			if test_common_dir(t3, items):
				return t3
			else:
				pos += 1
		if pos <= depth:
			t4 = os.path.dirname(t3)
			if self.test_common_dir(t4):
				return t4
			else:
				pos += 1
		#if not common directory found after 4 tries, fail as sparse directory.
		return None


	def next(self):
		if self.current is None:
			self.current = self.playlist[0]
			return self.current
		if self.loop_one:
			self.current = self.playlist[0]
			return self.current
		elif self.loop_all:
			if len(self.playlist) > 0:
				self.last.append(self.playlist.pop(0))
				self.current = self.playlist[0]
				return self.current
			else:
				log("Reached end of playlist! Restarting... (loop_all=True)")
				self.playlist = self.last
				self.last = []
				self.current = self.playlist[0]
				return self.current
		else:	
			l = len(self.playlist)
			if l == 1:
				if self.media_path is not None:
					self.playlist = self.load_directory(self.media_path)
					if self.shuffle:
						random(self.playlist)	
						log("Rebuilt playlist from {self.media_path}!", 'info')
					else:
						self.playlist = sorted(self.playlist)
					self.current = self.playlist[0]
					return self.current
			elif l > 1:
				print("playlist length:", l)
				self.last.append(self.playlist.pop(0))
				self.current = self.playlist[0]
				return self.current

	def previous(self):
		if self.loop_one:
			self.current = self.playlist[0]
			return self.current
		elif self.loop_all:
			if len(self.last) > 0:
				self.playlist.append(self.last.pop(0))
				self.current = self.playlist[0]
				return self.current
			else:
				log(f"Reached end of history!")
				self.current = self.playlist[0]
				return self.current
		else:
			l = len(self.last)
			if l == 0:
				log(f"Reached end of history!")
				self.current = self.playlist[0]
				return self.current
			else:
				#reverse history
				self.last.reverse()
				self.playlist.reverse()
				#transfer item
				self.playlist.append(self.last.pop(0))
				#un-reverse history
				self.last.reverse()
				self.playlist.reverse()
				self.current = self.playlist[0]
				return self.current


class playlist_old():
	def __init__(self, items=None, save=True, shuffle=True, loop_one=False, loop_all=False):
		self.current = None
		self.current_idx = -1
		self.loop_one = loop_one
		self.loop_all = loop_all
		self.last = []
		self.save = save
		self.shuffle = shuffle
		if items is None:
			self.playlist = []
		else:
			print("items:", len(items))
			self.playlist = self.set(playlist=items)

	def set(self, playlist=None, playlist_file=None):
		if playlist is not None:
			if type(playlist) != list:
				try:
					self.playlist = list(playlist)
				except Exception as e:
					log(f"playlist():provided playlist object not a list! ({e})", 'error')
			else:
				self.playlist = playlist
		elif playlist_file is not None:
			self.playlist = load_playlist_file(playlist_file)
		else:
			self.playlist = []
		if len(self.playlist) > 0 and self.shuffle:
			random(self.playlist)
		log(f"playlist.set():Playlist data set!", 'info')
		self.current_idx = 0
		self.current = self.playlist[0]
		self.last = []
		return self.playlist


	def add(self, filepath):
		self.playlist.append(filepath)
		self.current = filepath
		self.current_idx = self.playlist.index(filepath)
		return
		
	def clear(self):
		self.playlist = []
		self.currnet = None
		self.current_idx = 0
		log(f"playlist():playlist cleared!", 'info')
		return

	def next(self):
		if len(self.playlist) == 0:
			log(f"No files in playlist yet!", 'warning')
			return None
		elif len(self.playlist) == 1:
			conf = readConf()
			self.current = self.playlist[0]
			return self.current
		else:
			log(f"loop one:{self.loop_one}, loop_all:{self.loop_all}", 'info')
			if self.loop_one:
				# if repeat one...
				if self.current is None:
					#init current idx to first playlist item
					self.current = self.playlist[0]
					#return early to avoid saving one item to playlist
					return self.current
				else:
					#else leave current unchanged, and set idx to current index
					pass
			elif self.loop_all:
				self.last.append(self.playlist.pop(0))
				self.current = self.playlist[0]
			elif not self.loop_one and not self.loop_all:
				if len(self.playlist) <= 1:
					self.playlist = self.last
					self.last = []
					self.current = self.playlist[0]
					log(f"Playlist restarted!", 'info')
				else:
					self.last.append(self.playlist.pop(0))
					self.current = self.playlist[0]
		if self.save:
			save_playlist(self.playlist)
		return self.current

	def previous(self):
		if len(self.last) > 0:
			self.playlist.append(self.last.pop(0))
			self.current = self.playlist[0]
		elif len(self.last) == 0:
			log(f"Reached beginning of history! Rebuilding...")
			idx = len(self.playlist) - 1
			path = os.path.dirname(os.path.dirname(self.playlist[idx]))
			self.playlist = load_directory(path)
			if self.shuffle:
				random(self.playlist)
			self.last = [self.current]
			self.current = self.playlist[0]
		return self.current




def sqlite3(query):
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	com = f"sqlite3 \"{dbfile}\" \"{query}\""
	try:
		ret = subprocess.check_output(com, shell=True).decode().strip().replace('|', ':')
		if ret != '':
			if '::' in ret:
				ret = ret.replace('::', ':None:')
			if "\n" in ret:
				ret = ret.split("\n")
			return ret
		else:
			return None
	except Exception as e:
		#log(f"Error: sqlite3 command failed! {e}", 'error')
		return None

def splittolist(s):
	#checks string for common delimeters, and splits accordingly. If not found, assumes single item and wraps as list.
	if type(s) == tuple:
		#test if provided argument is a tuple (iterable), and transform to list if true
		return tuple(s)
	if ', ' in s:
		splitter = ', '
	elif ',' in s and ', ' not in s:
		splitter = ','
	elif ':' in s:
		splitter = ':'
	elif '|' in s:
		splitter = '|'
	else:
		splitter = None
	if splitter is None:
		return [s]
	else:
		return s.split(splitter)

def joinlist(l, joiner=', '):
	return joiner.join(l)

def is_npstring(string):
	if 'movies' in string or 'series' in string or 'music' in string and ':' in string:
		return True
	elif '/' in string and '.' in string:
		return False

def get_movies(shuffle=False, include_inactive=False, sort=None):
	if sort is None:
		sort = "title"
	else:
		if type(sort) == list:
			sort = joinlist(sort)
	if not include_inactive:
		movies = sqlite3(f"select filepath from movies where isactive = 1 order by {sort};")
	else:
		movies = sqlite3(f"select filepath from movies order by {sort};")
	if shuffle:
		random(movies)
	return movies

def get_music(shuffle=False, include_inactive=False, sort=None):
	if sort is None:
		sort = "artist, title"
	else:
		if type(sort) == list:
			sort = joinlist(sort)
	if not include_inactive:
		songs = sqlite3(f"select filepath from music where isactive = 1 order by {sort};")
	else:
		songs = sqlite3(f"select filepath from music order by {sort};")
	if shuffle:
		random(songs)
	return songs

def get_all_episodes(shuffle=False, include_inactive=False, sort=None):
	if sort is None:
		sort = "series_name, season, episode_number"
	else:
		if type(sort) == list:
			sort = joinlist(sort)
	if not include_inactive:
		series = sqlite3(f"select filepath from series where isactive = 1 order by {sort};")
	elif include_inactive:
		series = sqlite3(f"select filepath from series order by {sort};")
	if shuffle:
		random(series)
	return series

def get_episodes(series_name, shuffle=False, include_inactive=False, sort=None):
	if sort is None:
		sort = "season, episode_number"
	else:
		if type(sort) == list:
			sort = joinlist(sort)
	if not include_inactive:
		episodes = sqlite3(f"select filepath from series where series_name like '%{series_name}%' and isactive = 1 order by {sort};")
	elif include_inactive:
		episodes = sqlite3(f"select filepath from series where series_name like '%{series_name}%' order by {sort};")
	if shuffle:
		random(episodes)
	return episodes

def get_series_names(shuffle=False, include_inactive=False, sort=None):
	if sort is None:
		sort = "series_name"
	else:
		if type(sort) == list:
			sort = joinlist(sort)
	if not include_inactive:
		series_names = sqlite3(f"select distinct series_name from series where isactive = 1 order by {sort};")
	else:
		series_names = sqlite3(f"select distinct series_name from series order by {sort};")
	if shuffle:
		random(series_names)
	return series_names

def path_from_npstring(string):
	idx = string.split(':')[len(string.split(':')) - 1]
	table = string.split(':')[0]
	qstring = f"id = \'{idx}\'"
	return querydb(table=table, column='filepath', query=qstring)[0][0]


def npstring_from_path(path):
	string = None
	qstring = f"filepath = \"{path}\""
	in_series = querydb(table='series', column='series_name,season,episode_number,episode_name,id', query=qstring)
	in_movies = querydb(table='movies', column='title,year,id', query=qstring)
	in_music = querydb(table='music', column='artist,title,album,id', query=qstring)
	if in_series != []:
		string = f"series:{in_series[0][0]}:{in_series[0][1]}:{in_series[0][2]}:{in_series[0][3]}:{in_series[0][4]}"
	elif in_movies != []:
		string = f"movies:{in_movies[0][0]}:{in_movies[0][1]}:{in_movies[0][2]}"
	elif in_music != []:
		string = f"music:{in_music[0][0]}:{in_music[0][1]}:{in_music[0][2]}:{in_music[0][3]}"
	return string

def test_isnpstring(filepath):
	npstring = npstring_from_path(filepath)
	if npstring is not None:
		return True
	else:
		return False

def load_playlist(filepath=None):
	if filepath is None:
		filepath = os.path.join(os.path.expanduser("~"), '.np', 'current_playlist.dat')
	if os.path.exists(filepath):
		with open(filepath, 'rb') as f:
			items = pickle.load(f)
			f.close()
		return True, items
	else:
		log(f"playlist.load_playlist():Error: No playlist file found! Plese save items first!", 'error')
		return False, []

def save_playlist(items, filepath=None):
	try:
		if filepath is None:
			filepath = os.path.join(os.path.expanduser("~"), '.np', 'current_playlist.dat')
		with open(filepath, 'wb') as f:
			pickle.dump(items, f)
			f.close()
		return True
	except Exception as e:
		log(f"playlist.save_playlist:Error: Couldn't save to playlist:{e}! filepath={filepath}", 'error')
		return False


def get_next_series(series_name=None, shuffle=True):
	#if no series_name provided, grabs random name and tries to pull from history.
	#if history fails, it grabs all episodes in db and starts with 0. updates history at end.
	h = read_temp_history()
	j = "\n"
	if series_name is None:
		series_name = get_series_names(shuffle=True)[0]
	try:
		last = h[series_name]
	except:
		last = get_episodes(series_name=series_name)[0]
	if last is None or last == '':
		last = sqlite3(f"select filepath from series where series_name like \'%{series_name}%\' and isactive = 1 order by season,episode_number;")[0]
		h[series_name] = last
		write_temp_history(h)
	try:
		#get all episodes of a series_name, split by last, and grab next item
		episodes = get_episodes(series_name=series_name)
		out = j.join(episodes)
		try:	
			#try to get next in list. if fails, reset to 0
			next = out.split(last)[1].strip().split("\n")[0]
		except:
			next = episodes[0]
		#update history with current next value
		h[series_name] = next
		write_temp_history(h)
		return series_name, next
	except Exception as e:
		log(f"Error getting next series:{e}! last:{last}, series_name:{series_name}", 'error')
		return None


def reset_series_history(series_names=None, write_changes=True):
	h = read_temp_history()
	if series_names is not None:
		if type(series_names) != list:
			series_names = [series_names]
	else:
		series_names = get_series_names()
	for series_name in series_names:
		h[series_name] = get_episodes(series_name=series_name)[0]
	if write_changes:
		write_temp_history(h)
		log(f"playlist_utils.reset_series_history():Updated history file!", 'info')
	return h


def get_random_table(tables=None):
	# returns random table from either a provided list or all tables in database.
	if tables is None:
		tables = ['series', 'movies', 'music']
	if type(tables) == str:
		if ',' in tables:
			tables = tables.split(',')
		elif ', ' in tables:
			tables = tables.split(', ')
		else:
			tables = [tables]
	#create random integer index from table length
	pos = randint(0, len(tables) - 1)
	return tables[pos]

def build_playlist(play_mode=None, items=None, tables=None, max_items=200, shuffle=False, ret_type=None, new=False, save=True):
	ret = create_temp_history()
	if ret_type is not None:
		if ret_type != 'playlist' and ret_type != 'items':
			log(f"Error: Playlist return type must be 'playlist' or 'items'! Defaulting to 'playlist'...", 'error')
			ret_type = 'playlist'
	else:
		ret_type = 'playlist'
	conf = readConf()
	
	# get play mode and init playlist object accordingly.
	if play_mode is None:
		play_mode = conf['play_mode']
	if play_mode == 'database':
		pl = db_playlist()
	elif play_mode == 'playlist':
		pl = playlist(items=items)
		return pl
	if tables is None:
		#if tables is None, grab current play_type from conf and create list object
		tables = [conf['play_type']]
	else:
		#if tables is not a list, send to splittolist
		if type(tables) != list:
			tables = splittolist(tables)		
	# if items is included, check type is list, splittolist if not. if not provided, create empty list
	if items is not None:
		if type(items) != list:
			items = splittolist(items)
			pos = len(items) - 1
	else:
		if not new:
			# if items not included, check curent playlist dat file and load items.
			ret, items = load_playlist()
			if not ret:
				items = []
				pos = 0
			else:
				if type(items) == str:
					items = [items]
				pos = len(items)
				log(f"playlist_utils.build_playlist():loaded playlist items! ret:{ret}, len(items):{pos}", 'info')
		else:
			items = []
			pos = 0
	#grab current resume and insert at beginning of list
	resume_file = readConf()['nowplaying']['filepath']
	resume_file = npstring_from_path(resume_file)
	if resume_file is not None:
		if resume_file not in items:
			items.reverse()
			items.append(resume_file)
			items.reverse()
	if pos >= max_items:
		# if max items already exceeded (previous playlist loaded)...0000000000
		log(f"Already have a full playlist!", 'warning')
		save = False
	else:
		save = True
		movielist = get_movies()
		musiclist = get_music()
		#iterate through max items range and create playlist from random selected tables
		for i in range(pos, max_items):
			log(f"Adding playlist item:{i}/{max_items}", 'info')
			table = get_random_table(tables)
			if table == 'series':
				series_name, filepath = get_next_series(shuffle=shuffle)
				if filepath is not None:
					npstring = npstring_from_path(filepath)
					if npstring is not None:
						items.append(npstring)
			elif table == 'movies':
				try:
					filepath = movielist.pop(0)
					items.append(npstring_from_path(filepath))
				except:
					log(f"All movies in list added!", 'info')
					break
			elif table == 'music':
				try:
					filepath = musiclist.pop(0)
					items.append(npstring_from_path(filepath))
				except:
					log(f"All music in list added!", 'info')
					break
	#remove temp history file
	rm_temp_history()
	if shuffle:
		# if shuffle, randomize items list
		random(items)
	#return simple list of item filepaths for use in playlist.set()
	if save:
		log(f"playlist_utils.build_playlist():Playlist saved!", 'info')
		save_playlist(items)
	if ret_type == 'items':
		return items
	elif ret_type == 'playlist':
		return pl.set(items)
