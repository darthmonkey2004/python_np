from np.core.core import read_history, write_history
from random import randint, shuffle
from np.utils.searchdb import *
from np.core.nplayer_db import querydb
from np.core.core import create_media
from np.core.log import np_logger

log = np_logger().log_msg
h = read_history()
class db_playlist():
	def __init__(self, _list=None):
		self.current = None
		self.current_idx = 0
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
		return self


	def path_from_npstring(self, string):
		idx = string.split(':')[len(string.split(':')) - 1]
		table = string.split(':')[0]
		qstring = f"id = \'{idx}\'"
		return querydb(table=table, column='filepath', query=qstring)[0][0]


	def npstring_from_path(self, path):
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
			string = f"music:{im_music[0][0]}:{im_music[0][1]}:{im_music[0][2]}:{im_music[0][3]}"
		return string


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
		if 'series' in self.current or 'movies' in self.current or 'music' in self.current:
			self.current = self.path_from_npstring(self.current)
		return self.current

	def previous(self):
		if self.current is None:
			self.current = self.next()
		if 'movies' not in self.current or 'series' not in self.current or 'music' not in self.current:
			idx = self.playlist.index(self.npstring_from_path(self.current)) - 1
		else:
			idx = self.playlist.index(self.current) - 1
		if idx >= 0:
			self.current_idx = idx
			self.current = self.playlist[self.current_idx]
		else:
			log(f"playlist():No previous item available!", 'warning')
		if 'movies' in self.current or 'series' in self.current or 'music' in self.current:
			self.current = self.path_from_npstring(self.current)
		return self.current


class playlist():
	def __init__(self, _list=None):
		self.current = None
		self.current_idx = 0
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
		return self.current

	def previous(self):
		idx = self.playlist.index(self.current) - 1
		if idx >= 0:
			self.current_idx = idx
			self.current = self.playlist[self.current_idx]
		else:
			log(f"playlist():No previous item available!", 'warning')
		return self.current


def random_series_name():
	items = sqlite3("select distinct series_name from series;")
	shuffle(items)
	return items[0]
	
def get_next_series(series_name=None):
	global h
	j = "\n"
	if series_name is None:
		series_name = random_series_name()
	last = h[series_name]
	if last is None or last == '':
		last = sqlite3(f"select filepath from series where series_name like \'%{series_name}%\' order by season,episode_number;")[0]
		h[series_name] = last
		#write_history(h)
	out = j.join(sqlite3(f"select filepath from series where series_name like \'%{series_name}%\' order by season, episode_number;"))
	next = out.split(last)[1].strip().split("\n")[0]
	h[series_name] = next
	#write_history(h)
	return series_name, next

def get_next_movies(title=None):
	movies = sqlite3("select filepath from movies;")
	shuffle(movies)
	return movies[0]

def get_next_music():
	songs = sqlite3("select filepath from music;")
	shuffle (songs)
	return songs[0]


def reset_series_history():
	global h
	for series_name in list(h.keys()):
		files = sqlite3(f"select filepath from series where series_name like \'%{series_name}%\' order by season,episode_number;")
		try:
			last = files[0]
		except:
			last = None
		if last is None:
			break
		else:
			h[series_name] = last



def new_rdm(tables=None):
	global h
	pl = db_playlist()
	if tables is None:
		tables = ['series', 'movies']
	if type(tables) != list:
		tables = [tables]
	ct = 100
	pos = 0
	items = []
	while pos < ct:
		pos += 1
		table = tables[randint(0, len(tables) - 1)]
		if table == 'series':
			series_name, next = get_next_series()
			if next is not None:
				string = pl.npstring_from_path(next)
				items.append(string)
			else:
				last = sqlite3(f"select filepath from series where series_name like \'%{series_name}%\' order by season,episode_number;")[0]
				if last is not None and last != '':
					h[series_name] = last
					write_history(h)
			
			#except Exception as e:
			#	log(f"Reached end of series list ({e})! Starting from 0...", 'warning')
			#	items.append(sqlite3(f"select filepath from series where series_name like \'%{series_name}%\' order by season,episode_number;")[0])
		elif table == 'movies':
			try:
				string = pl.npstring_from_path(get_next_movies())
				items.append(string)
			except Exception as e:
				log(f"Reached end of movies list ({e})! Starting from 0...", 'warning')
				string = pl.npstring_from_path(sqlite3("select filepath from movies;")[0])
				items.append(string)
		elif table == 'music':
			try:
				items.append(get_next_music())
			except Exception as e:
				log(f"Reached end of music list ({e})! Starting from 0...", 'warning')
				items.append(sqlite3("select filepath from music;")[0])
	return pl.set(items)
		
if __name__ == "__main__":
	hlist = create_media()
	his = playlist(hlist)
	print(his.playlist, his.current, his.current_idx)
		
