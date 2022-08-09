import os
from os.path import basename
import np
import subprocess

#TODO: add manual entry section if lookup fails to retreive movie data.

def scan_movies(target_dir=None):
	exts = ['mp4', 'mov', 'avi', 'flv']
	np.test_db()
	conf = np.readConf()
	if target_dir == None:
		target_dir = conf['media_directories']['movies']
	for ext in exts:
		com = (f"find '{target_dir}' -name '*.{ext}'")
		files = subprocess.check_output(com, shell=True).decode().strip()
		files = files.split("\n")
		for filepath in files:
			print (f"Adding file: {filepath}")
			par = os.path.dirname(filepath)
			title = os.path.basename(par).split('(')[0].strip()
			data = np.lookup_movies(title)
			if data is None:
				print ("Error on lookup, need to add manually. TODO!")
				pass
			else:
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
				sql_string = (f"INSERT into movies (isactive, tmdbid, title, year, release_date, duration, description, poster, filepath) VALUES (1, '{data['tmdbid']}', '{data['title']}', {data['year']}, '{data['release_date']}', '{data['duration']}', '{data['description']}', '{data['poster']}', '{filepath}');")
				print (sql_string)
				ret = np.addtodb('movies', sql_string)
				if ret == True:
					print ("Ok!")
				else:
					print (ret)
					input()

if __name__ == "__main__":
	import sys
	scan_movies(sys.argv[1])
