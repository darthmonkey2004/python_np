import pickle
from np.core.core import read_history, write_history
from random import randint, shuffle
from np.utils.searchdb import *
from np.core.nplayer_db import querydb
from np.core.core import create_media
from np.core.log import np_logger
from np.core.conf import readConf

log = np_logger().log_msg
h = read_history()
class db_playlist():
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
		log(f"db_playlist.set():Playlist data set!", 'info')
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
		self.last = self.current
		print(f"self.current_idx:{self.current_idx}")
		if len(self.playlist) == 0:
			log(f"No files in playlist yet!", 'warning')
			return None
		elif len(self.playlist) == 1:
			self.current_idx = 0
			self.current = self.playlist[self.current_idx]
		else:
			self.current_idx += 1
			try:
				self.current = self.playlist[self.current_idx]
			except Exception as e:
				self.current = self.playlist[0]
				self.current_idx = 0
				log(f"Reached end of playlist! ({e}). Using 0...", 'warning')
		print(self.current, self.current_idx)
		if self.current is None:
			try:
				name = sqlite3(f"select series_name from series where filepath like '%{self.last}%';")
				self.current = reset_series_history(name)
				log(f"Reached end of playlist. Using index 0 for {name}...", 'warning')
			except:
				from random import shuffle
				h = read_history()
				l = list(h.values())
				shuffle(l)
				self.current = l[0]
				self.last = self.current
				self.idx = 0
		if 'series' in self.current or 'movies' in self.current or 'music' in self.current:
			self.current = self.path_from_npstring(self.current)
		self.playlist = self.playlist[self.current_idx:]
		save_playlist(self.playlist)
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
		if self.current is None:
			log(f"playlist.previous():self.current returned None!", 'error')
			return None
		if 'movies' in self.current or 'series' in self.current or 'music' in self.current:
			self.current = self.path_from_npstring(self.current)
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
		print("data:", playlist)
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


def random_series_name():
	items = sqlite3("select distinct series_name from series where isactive = 1;")
	shuffle(items)
	return items[0]
	
def get_next_series(series_name=None):
	global h
	j = "\n"
	if series_name is None:
		series_name = random_series_name()
	try:
		last = h[series_name]
	except:
		last = None
	if last is None or last == '':
		last = sqlite3(f"select filepath from series where series_name like \'%{series_name}%\' and isactive = 1 order by season,episode_number;")[0]
		h[series_name] = last
		#write_history(h)
	try:
		out = j.join(sqlite3(f"select filepath from series where series_name like \'%{series_name}%\' and isactive = 1 order by season, episode_number;"))
		next = out.split(last)[1].strip().split("\n")[0]
		h[series_name] = next
		return series_name, next
	except Exception as e:
		log(f"Error getting next series:{e}! last:{last}, series_name:{series_name}", 'error')
		return None

def get_shuffle_movies(title=None):
	movies = sqlite3("select filepath from movies where isactive = 1;")
	shuffle(movies)
	return movies

def get_shuffle_music():
	songs = sqlite3("select filepath from music where isactive = 1;")
	shuffle (songs)
	return songs


def reset_series_history(name=None):
	global h
	h = read_history()
	print("name:", name)
	if name is None:
		for series_name in list(h.keys()):
			files = sqlite3(f"select filepath from series where series_name like \'%{series_name}%\' and isactive = 1 order by season,episode_number;")
			try:
				last = files[0]
			except:
				last = None
			if last is None:
				txt = f"playlist.reset_series_history:Exception getting series file list: {name}, items={files}"
				raise Exception(ValueError, txt)
				return False
			else:
				h[series_name] = last
	elif name is not None:
		files = sqlite3(f"select filepath from series where series_name like '%{name}%' and isactive = 1 order by season,episode_number;")
		try:
			last = files[0]
		except:
			raise Exception(ValueError, f"playlist.reset_series_history:Exception getting series file list: {name}, items={files}")
			return False
		h[name] = last
		write_history(h)
		return last

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



def new_rdm(tables=None):
	movies = get_shuffle_movies()
	music = get_shuffle_music()
	global h
	pl = db_playlist()
	if tables is None:
		tables = ['series', 'movies']
	if type(tables) != list:
		tables = [tables]
	ct = 300
	pos = 0
	items = []
	ret, items = load_playlist()
	if ret:
		log(f"Playlist loaded!", 'info')
		l = []
		print("Loaded playlist items:", items)
		
		return pl.set(items)
	try:
		conf = readConf()
		items.append(npstring_from_path(conf['nowplaying']['filepath']))
	except:
		pass
	musicpos = -1
	moviespos = -1
	while pos < ct:
		pos += 1
		table = tables[randint(0, len(tables) - 1)]
		if table == 'series':
			next = None
			while next is None:
				try:
					series_name, next = get_next_series()
					if next == '':
						next = None
				except Exception as e:
					next = None
					log(f"Unable to get next (None) for series:{series_name} {e}", 'error')
					
			if next is not None:
				string = pl.npstring_from_path(next)
				items.append(string)
			else:
				log(f"Next is None for:{series_name}", 'info')
				last = sqlite3(f"select filepath from series where series_name like \'%{series_name}%\' where isactive = 1 order by season,episode_number;")[0]
				if last is not None and last != '':
					h[series_name] = last
					write_history(h)
				items.append(last)
		elif table == 'movies':
			try:
				moviespos += 1
				string = pl.npstring_from_path(movies[moviespos])
				items.append(string)
			except Exception as e:
				log(f"Reached end of movies list ({e})! Starting from 0...", 'warning')
				moviespos = 0
				string = pl.npstring_from_path(movies[moviespos])
				items.append(string)
		elif table == 'music':
			try:
				musicpos += 1
				items.append(music[musicpos])
			except Exception as e:
				log(f"Reached end of music list ({e})! Starting from 0...", 'warning')
				musicpos = 0
				items.append(music[musicpos])
	log(f"playlist.new_rdm():new random playlist created! tables={tables}", 'info')
	ret = save_playlist(items)
	if not ret:
		log(f"playlist.new_rdm():Playlist failed to save....", 'warning')
	return pl.set(items)

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
	
	
		


if __name__ == "__main__":
	hlist = create_media()
	his = playlist(hlist)
	#print(his.playlist, his.current, his.current_idx)
		
