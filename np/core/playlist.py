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


class db_playlist():
	def __init__(self, _list=None):
		self.playlist_min_ct = 20
		self.last = []
		self.current = None
		if _list is None:
			self.playlist = []
		else:
			self.playlist = self.set(_list)

	def set(self, playlist=None):
		if playlist is not None:
			if type(playlist) != list:
				try:
					self.playlist = list(playlist)
				except Exception as e:
					log(f"playlist():provided playlist object not a list! ({e})", 'error')
			else:
				self.playlist = playlist
		else:
			self.playlist = []
		log(f"db_playlist.set():Playlist data set!", 'info')
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
		# pop item 0 from playlist...
		last = self.playlist.pop(0)
		if len(self.playlist) <= self.playlist_min_ct:
			#if minimum playlist items reached, execute build and append to current
			self.playlist = build_playlist(items=self.playlist)
			
			#update current saved playlist in pickle dat file
			save_playlist(self.playlist)
		self.last.append(last)# and store in last list

		#if we haven't reached the end of playlist...
		if len(self.playlist) > 0:

			# set current to 0
			self.current = self.playlist[0]
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
	def __init__(self, _list=None):
		self.current = None
		self.current_idx = -1
		if _list is None:
			self.playlist = []
		else:
			self.playlist = self.set(_list)

	def set(self, playlist=None):
		if playlist is not None:
			if type(playlist) != list:
				try:
					self.playlist = list(playlist)
				except Exception as e:
					log(f"playlist():provided playlist object not a list! ({e})", 'error')
			else:
				self.playlist = playlist
		else:
			self.playlist = []
		log(f"playlist.set():Playlist data set!", 'info')
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
			self.current_idx = 1
		else:
			self.current_idx += 1
			try:
				self.current = self.playlist[self.current_idx]
			except Exception as e:
				self.current = self.playlist[0]
				self.current_idx = 0
				log(f"Reached end of playlist! ({e}). Using 0...", 'warning')
		self.playlist = self.playlist[self.current_idx:]
		save_playlist(self.playlist)
		return self.current

	def previous(self):
		idx = self.playlist.index(self.current) - 1
		if idx >= 0:
			self.current_idx = idx
			self.current = self.playlist[self.current_idx]
		else:
			log(f"playlist():No previous item available!", 'warning')
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
	h = read_history()
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
		write_history(h)
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
		write_history(h)
		return series_name, next
	except Exception as e:
		log(f"Error getting next series:{e}! last:{last}, series_name:{series_name}", 'error')
		return None


def reset_series_history(series_names=None, write_changes=True):
	h = read_history()
	if series_names is not None:
		if type(series_names) != list:
			series_names = [series_names]
	else:
		series_names = get_series_names()
	for series_name in series_names:
		h[series_name] = get_episodes(series_name=series_name)[0]
	if write_changes:
		write_history(h)
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

def build_playlist(play_mode=None, items=None, tables=None, max_items=200, shuffle=True, ret_type=None, new=False, save=True):
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
		pl = playlist(items)
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
			i = len(items) - 1
	else:
		if not new:
			# if items not included, check curent playlist dat file and load items.
			ret, items = load_playlist()
			log(f"playlist_utils.build_playlist():loaded playlist items! ret:{ret}, items:{items}", 'info')
			if not ret:
				items = []
				i = 0
			else:
				i = len(items) - 1
		else:
			items = []
			i = 0
	if i >= max_items:
		# if max items already exceeded (previous playlist loaded)...0000000000
		log(f"Already have a full playlist!", 'warning')
	else:
		movielist = get_movies()
		musiclist = get_music()
		#iterate through max items range and create playlist from random selected tables
		for i in range(max_items):
			table = get_random_table(tables)
			if table == 'series':
				series_name, filepath = get_next_series(shuffle=shuffle)
				items.append(npstring_from_path(filepath))
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
	#return simple list of item filepaths for use in playlist.set()
	if save:
		log(f"playlist_utils.build_playlist():Playlist saved!", 'info')
		save_playlist(items)
	if ret_type == 'items':
		return items
	elif ret_type == 'playlist':
		return pl.set(items)
