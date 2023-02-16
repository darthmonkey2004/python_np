from urllib.parse import quote, unquote
import requests
import subprocess
import os
from np.core.conf import readConf
from np.core.nplayer_db import test_db
from np.core.nplayer_db import addtodb
from np.utils.cleandb import run as cleandb
from np.utils.tadb_search import lookup
from np.utils.id3 import tag
from np.core.log import np_logger
from np.core.nplayer_db import get_columns
log = np_logger().log_msg
id3 = tag()

def set_empty(play_type):
	pragma = get_columns(play_type)
	columns = list(pragma.keys())
	info = {}
	for key in columns:
		dtype = pragma[key]['data_type']
		if dtype == 'INTEGER' or dtype == 'BOOL':
			info[key] = 0
		elif dtype == 'TEXT':
			info[key] = 'Unknown'
	return info



def test_exists(filepath):
	conf = readConf()
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	com = (f"sqlite3 \"{dbfile}\" \"select id from music where filepath = '{filepath}'\";")
	exists = subprocess.check_output(com, shell=True).decode().strip()
	if conf['debug'] == True:
		log(f"exists: {exists}, filepath: {filepath}", 'debug')
	if exists != '':
		return True
	else:
		return False


def get_url(artist, title):
	test='https://www.google.com/imgres?imgurl='
	s = '&amp;imgrefurl'
	img_url = None
	query = (artist + " " + title + " album art")
	q = quote(query)
	url = ("https://www.google.com/search?q=" + q)
	r = requests.get(url)
	data = r.text.split("\n")
	for item in data:
		if test in item:
			img_url = item.split(test)[1].split(s)[0]
			if '%' in img_url:
				img_url = unquote(img_url)
			break
	return img_url


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
		exists = test_exists(filepath)
		if exists == True:
			log(f"Already in database: '{filepath}'", 'debug')
		else:
			info = set_empty('music')
			hastag = True
			tag_data = {}
			title = None
			artist = None
			txt = ("Progress: (" + str(pos) + "/" + str(ct) + ", filepath:" + filepath)
			audiofile = None
			log(f"{txt}", 'debug')
			if filepath == '' or not os.path.exists(filepath):
				log("Error: No file path provided (directory might be empty?)", 'info')
				break
			tag = id3.read(filepath)
			try:
				title = tag.title
				artist = tag.artist
				hastag = True
			except:
				title = None
				artist = None
				hastag = False
			if tag is None:
				pass
			else:
				if tag.title is None or tag.artist is None or hastag == False:
					split = (f"{target_dir}/")
					fname = filepath.split(split)[1]
					if '[' in fname:
						if tag.title is None:
							tag.title = fname.split('[')[0].strip()
						if tag.artist is None:
							s = ' - '
							tag.artist = fname.split(s)[1].split('.')[0]
					else:
						s = ' - '
						try:
							if tag.title is None:
								tag.title = fname.split(s)[0]
							if tag.artist is None:
								tag.artist = fname.split(s)[1].split('.')[0]
						except:
							log(f"File: '{filepath}' - Unable to parse info from path.", 'error')
							tag.title = input("Enter artist name: ")
							tag.artist = input("Enter song title: ")
				info = lookup(tag.artist, tag.title)

			if info['artist'] != 'Unknown':
				tag.artist = info['artist']
			else:
				if tag.artist == None:
					tag.artist = input("Enter artist:")
			if info['album'] != 'Unknown':
				tag.album = info['album']
			else:
				if tag.album == None:
					tag.artist = input("Enter artist:")
			if info['track'] != 'Unknown':
				tag.track = info['track']
			else:
				track = 0
			if info['album_id'] != "Unknown":
				tag.album_id = info['album_id']
			if info['artist_id'] != "Unknown":
				tag.artist_id = info['artist_id']
			if info['genre'] != "Unknown":
				tag.genre = info['genre']
			if info['mbid'] != "Unknown":
				tag.mbid = info['mbid']
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
			poster = get_url(info['artist'], info['title'])
			if poster is None:
				poster = 'Unknown'
			info['poster'] = poster

			sql_string = (f"INSERT INTO music (isactive, title, mbid, album, album_id, artist_id, artist, genre, track, filepath, poster) VALUES({isactive}, '{title}', '{mbid}', '{album}', '{album_id}', '{artist_id}', '{artist}', '{genre}', {track}, '{filepath}', '{poster}');")
			ret = addtodb('music', sql_string)
			if conf['debug'] == True:
				log(f"Add to db results: {ret}, filepath:{filepath}", 'info')
			if ret is not True:
				log(f"Add to db returned data: {ret}", 'warning')
	log(f"Running cleandb: 'music'...", 'info')
	cleandb('music')

if __name__ == "__main__":
	ret = scan_music()
	log(f"Results: {ret}",'info')
