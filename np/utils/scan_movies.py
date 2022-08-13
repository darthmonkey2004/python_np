import os
from os.path import basename
import np
import subprocess

#TODO: add manual entry section if lookup fails to retreive movie data.

conf = np.readConf()
def sqlite3(query):
	dbfile = (f"{np.DATA_DIR}{os.path.sep}nplayer.db")
	com = (f"sqlite3 '{dbfile}' \"{query}\"")
	out = subprocess.check_output(com, shell=True).decode().strip().split("\n")[0]
	if conf['debug'] == True:
		np.log(f"SQLITE3 Query: {query}", 'info')
		np.log(f"SQLITE3 Results: {out}", 'info')
	return out

def scan_movies(target_dir=None):
	exts = ['mp4', 'mov', 'avi', 'flv']
	np.test_db()
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
					np.log(f"Adding file: {filepath}", 'info')
					par = os.path.dirname(filepath)
					title = os.path.basename(par).split('(')[0].strip()
					if title == '':
						np.log(f"scan_movies.py:Title not set (trimmed from filepath): {filepath}", 'error')
						input("Press enter to continue...")
						return False
					data = np.lookup_movies(title)
					if data is None:
						np.log(f"scan_movies.py:Error on lookup, need to add manually. File: {filepath}", 'error')
						data = {}
						data['tmdbid'] = 'null'
						data['title'] = title
						data['year'] = 'null'
						data['release_date'] = 'null'
						data['duration'] = 'null'
						data['description'] = 'null'
						data['poster'] = 'null'
					else:
						try:
							if "'" in data['description']:
								chunks = data['description'].split("'")
								out = ''
								for chunk in chunks:
									out = (f"{out}{chunk}")
								data['description'] = out
							if "'" in data['title']:
								chunks = title.split("'")
								out = ''
								for chunk in chunks:
									out = (f"{out}{chunk}")
								data['title'] = out
						except Exception as e:
							data['tmdbid'] = 'null'
							data['title'] = title
							data['year'] = 'null'
							data['release_date'] = 'null'
							data['duration'] = 'null'
							data['description'] = 'null'
							data['poster'] = 'null'
							np.log(f"Exception in scan_movies.py: {e}", 'error')
					sql_string = (f"INSERT into movies (isactive, tmdbid, title, year, release_date, duration, description, poster, filepath) VALUES (1, '{data['tmdbid']}', '{data['title']}', {data['year']}, '{data['release_date']}', '{data['duration']}', '{data['description']}', '{data['poster']}', '{filepath}');")
					ret = np.addtodb('movies', sql_string)
					if ret == True:
						print ("Ok!")
					else:
						print (ret)
						input()
				else:
					np.log(f"File already in database! ({filepath}, Skipping..", 'info')

if __name__ == "__main__":
	import sys
	scan_movies(sys.argv[1])
