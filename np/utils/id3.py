import os
import subprocess

from np.core.log import np_logger
log = np_logger().log_msg

class id3():
	def __init__(self):
		self.title = None
		self.album = None
		self.artist = None
		self.year = None
		self.track = None
		self.comment = None
		self.filepath = None
		self.isactive = 1
		self.album_id = None
		self.artist_id = None
		self.mbid = None
		self.comment = None
		self.genre = None
		self.info = {}

class tag(id3):
	#updates an id3 tag in 'filepath'
	def save(self, filepath=None):
		if filepath is not None:
			self.filepath = filepath
		if self.filepath is None:
			log(f"Whoops! you must specify a file path at least once!", 'error')
			return False
		if not os.path.exists(self.filepath):
			log(f"File not found: {filepath}", 'error')
			self.filepath = None
			return False
		com = (f"id3 -t \"{self.title}\" -a \"{self.artist}\" -A \"{self.album}\" -y \"{self.year}\" -T \"{self.track}\" \"{self.filepath}\"")
		ret = subprocess.check_output(com, shell=True)
		if ret:
			log(ret, 'info')
		return True
	
	#returns a dictionary of all class attributes
	def get_info(self):
		if self.filepath is not None:
			self.read(self.filepath)
			self.info = {}
			self.info['isactive'] = 1
			self.info['title'] = self.title
			self.info['album'] = self.album
			self.info['results'] = False
			self.info['album_id'] = 'Unknown'
			self.info['artist_id'] = 'Unknown'
			self.info['artist'] = self.artist
			self.info['genre'] = self.genre
			self.info['track'] = self.track
			self.info['mbid'] = 'Unknown'
			self.info['filepath'] = self.filepath
			return self.info
		else:
			log(f"Error: Unable to read id3  tag. Details:No filepath set!", 'error')
			return None

	#reads tag data
	def read(self, filepath=None):
		if filepath == None:
			if self.filepath is not None:
				filepath = self.filepath
			else:
				log(f"Whoops! you must specify a file path at least once!", 'error')
				return False
		if os.path.exists(filepath):
			self.filepath = filepath
		else:
			log(f"File not found: {filepath}", 'error')
			self.filepath = None
			return False
		try:
			com = (f"id3 -R -l '{self.filepath}'")
			data = subprocess.check_output(com, shell=True).decode().strip().split("\n")
			for item in data:
				key = item.split(':')[0].strip()
				try:
					val = item.split(':')[1].strip()
				except:
					val = None
				if val == '' or val is None:
					val == 'Unknown'
				if key == 'Filename':
					self.filepath = val
				elif key == 'Title':
					self.title = val
				elif key == 'Artist':
					self.artist = val
				elif key == 'Album':
					self.album = val
				elif key == 'Year':
					self.year = val
				elif key == 'Genre':
					self.genre = val
				elif key == 'Track':
					self.track = val
				elif key == 'Comment':
					self.comment = val
			return self
			
		except Exception as e:
			log(f"Exception in id3.read: {e}", 'error')
			return None
	def clear(self, filepath=None):
		if filepath == None:
			pass
		else:
			if self.filepath is not None:
				filepath = self.filepath
			else:
				log(f"Whoops! you must specify a file path at least once!", 'error')
				return False
		if os.path.exists(filepath):
			self.filepath = filepath
		else:
			log(f"File not found: {filepath}", 'error')
			self.filepath = None
			return False
		try:
			com = (f"id3 -d '{self.filepath}'")
			ret = subprocess.check_output(com, shell=True).decode().strip().split("\n")
			if ret:
				log(ret, 'info')
			return True
		except Exception as e:
			log(f"Unable to clear tag in '{self.filepath}': {e}", 'error')
			return False
		
