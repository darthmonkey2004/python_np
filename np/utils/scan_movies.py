from np.utils.cleandb import run as cleandb
from np.core.nplayer_db import addtodb
import os
from os.path import basename
from np.core.log import np_logger
from np.core.conf import readConf
from np.core.nplayer_db import test_db
from np.utils.pbdl.query_movies import query_movies
import subprocess
log = np_logger().log_msg
data_dir = os.path.join(os.path.expanduser("~"), '.np')
#TODO: add manual entry section if lookup fails to retreive movie data.


def clean_string(string):
	chars = ['!', '@', '"', "'", ':', '^', '$']
	for char in chars:
		string = string.replace(char, '_')
	return string


conf = readConf()
def sqlite3(query):
	log(f"sqlite3 query running from scan_movies, query={query}", 'info')
	dbfile = os.path.join(data_dir, "nplayer.db")
	com = (f"sqlite3 '{dbfile}' \"{query}\"")
	out = subprocess.check_output(com, shell=True).decode().strip().split("\n")[0]
	if conf['debug'] == True:
		log(f"SQLITE3 Query: {query}, Results: {out}", 'info')
	return out

def scan_movies(target_dir=None):
	exts = ['mp4', 'mov', 'avi', 'flv']
	test_db()
	if target_dir == None:
		target_dir = conf['media_directories']['movies']
	for ext in exts:
		com = (f"find '{target_dir}' -name '*.{ext}'")
		files = subprocess.check_output(com, shell=True).decode().strip()
		files = files.split("\n")
		for filepath in files:
			if filepath is not None and filepath != '':
				data = None
				com = (f"select filepath from movies where filepath = '{filepath}';")
				exists = sqlite3(com)
				if exists == '':
					log(f"Adding file: {filepath}", 'info')
					par = os.path.dirname(filepath)
					title = os.path.basename(par).split('(')[0].strip()
					if title == '':
						log(f"scan_movies.py:Title not set (trimmed from filepath): {filepath}", 'error')
						title = input("Enter title: ")
					data = query_movies(title)
					if data is None:
						log(f"scan_movies.py:Error on lookup, need to add manually. File: {filepath}", 'error')
						data = {}
						data['tmdbid'] = 'null'
						data['title'] = clean_string(title)
						data['year'] = 'null'
						data['release_date'] = 'null'
						data['duration'] = 'null'
						data['description'] = 'null'
						data['poster'] = 'null'
					else:
						try:
							data['description'] = clean_string(data['description'])
							data['title'] = clean_string(data['title'])
						except Exception as e:
							data['tmdbid'] = 'null'
							data['title'] = clean_string(title)
							data['year'] = 'null'
							data['release_date'] = 'null'
							data['duration'] = 'null'
							data['description'] = 'null'
							data['poster'] = 'null'
							log(f"Exception in scan_movies.py: {e}", 'error')
					sql_string = (f"INSERT into movies (isactive, tmdbid, title, year, release_date, duration, description, poster, filepath) VALUES (1, '{data['tmdbid']}', '{data['title']}', {data['year']}, '{data['release_date']}', '{data['duration']}', '{data['description']}', '{data['poster']}', '{filepath}');")
					ret = addtodb('movies', sql_string)
					if ret == True:
						print ("Ok!")
					else:
						print (ret)
				else:
					log(f"File already in database! ({filepath}, Skipping..", 'info')
	log(f"Running cleandb: 'movies'...", 'info')
	cleandb('movies')

if __name__ == "__main__":
	import sys
	scan_movies(sys.argv[1])
