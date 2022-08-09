import subprocess
import eyed3
import os
from np import readConf, test_db, addtodb
from np.utils.tadb_search import lookup

def scan_music(target_dir=None):
	test_db()
	conf = readConf()
	if target_dir == None:
		target_dir = conf['media_directories']['music']
	com = ("find '" + target_dir + "' -name '*.mp3'")
	files = subprocess.check_output(com, shell=True).decode().strip()
	files = files.split("\n")
	needs_tagged = []
	ct = len(files)
	pos = 0
	for filepath in files:
		pos = pos + 1
		tag_data = {}
		title = None
		artist = None
		txt = ("Progress: (" + str(pos) + "/" + str(ct) + ", filepath:" + filepath)
		print (txt)
		if filepath == '':
			pass

		try:
			audiofile = eyed3.load(filepath)
			tag = audiofile.tag
		except:
			audiofile.initTag()
			tag_data = {}
			title = None
			artist = None

		if audiofile.tag is not None:
			tag_data['isactive'] = 1
			if tag.title is not None:
				tag_data['title'] = str(tag.title)
			if tag.album is not None:
				tag_data['album'] = str(tag.album)
			if tag.release_date is not None:
				tag_data['year'] = str(tag.release_date)
			if tag.artist is not None:
				tag_data['artist'] = str(tag.artist)
			if tag.track_num is not None:
				tag_data['track'] = tag.track_num
			tag_data['filepath'] = filepath
		else:
			audiofile.initTag()
			title = None
			artist = None

		if title is None or artist is None:
			split = (f"{target_dir}/")
			fname = filepath.split(split)[1]
			if '[' in fname:
				if title is None:
					title = fname.split('[')[0].strip()
				if artist is None:
					s = ' - '
					artist = fname.split(s)[1].split('.')[0]
			else:
				if title is None:
					title = fname.split(s)[0]
				if artist is None:
					artist = fname.split(s)[1].split('.')[0]
		info = lookup(artist, title)

		if info['artist'] is None:
			if tag_data['artist'] is None:
				tag_data['artist'] = input("Enter artist name:")
			tag.artist = tag_data['artist']
		else:
			tag.artist = info['artist']
		if info['album'] is None:
			if tag_data['album'] is None:
				tag_data['album'] = input("Enter album name:")
			tag.album = tag_data['album']
		else:
			tag.album = info['album']
		if info['title'] is None:
			if tag_data['title'] is None:
				tag_data['title'] = input("Enter title:")
			tag.title = tag_data['title']
		else:
			tag.title = info['title']
		if info['track'] is None:
			if tag_data['track'] is None:
				tag_data['track'] = input("Enter track:")
			tag.track = tag_data['track']
		else:
			tag.track = info['track']
		tag.save(filepath)
		isactive = info['isactive']
		title = info['title']
		mbid = info['mbid']
		album = info['album']
		album_id = info['album_id']
		artist_id = info['artist_id']
		artist = info['artist']
		genre = info['genre']
		track = info['track']

		sql_string = (f"INSERT INTO music (isactive, title, mbid, album, album_id, artist_id, artist, genre, track, filepath) VALUES({isactive}, '{title}', '{mbid}', '{album}', '{album_id}', '{artist_id}', '{artist}', '{genre}', {track}, '{filepath}');")
		print (sql_string)
		ret = addtodb('music', sql_string)
		if ret is not True:
			print (ret)

if __name__ == "__main__":
	ret = scan_music()
	print (ret)
