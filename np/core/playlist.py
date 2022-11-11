from np.core.nplayer_db import querydb
from np.core.core import create_media
from np.core.log import np_logger

log = np_logger().log_msg

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
		return self.playlist


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

if __name__ == "__main__":
	hlist = create_media()
	his = playlist(hlist)
	print(his.playlist, his.current, his.current_idx)
		
