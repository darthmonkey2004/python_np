from np.utils.scan_music import scan_music
from np.utils.scan_movies import scan_movies
from np.utils.scan_series import scan_series
from np.core.conf import readConf
from np.core.nplayer_db import create_db
from np.core.log import np_logger
from np.utils import cleandb
log = np_logger().log_msg
import subprocess
import os
import datetime
from np.utils.dbfixer import dbfixer
dbfixer = dbfixer()
data_dir = os.path.join(os.path.expanduser("~"), '.np')

todo = """TODO: put a try/except in scan_series line 127 (info = query_series(series_name, season, episode_number)),
	and get info from user. possibly get season/episode_data and show user to select from.
TODO: scan_series(): caught exception on unstructured file system(unparseable info from filename) should have triggered
user input for info, it didn't..... FIX ME..
TODO: Figure out a way to include certain movies in with the series, though technically is considered movie. Futurama, South Park both have them."""
print(todo)

def backup_db():
	ts = datetime.datetime.now().timestamp()
	newname = (f"{ts}.nplayer.backup.db")
	com = f"cd '{data_dir}'; mv nplayer.db {newname}"
	ret = subprocess.check_output(com, shell=True)
	if ret:
		return ret
	else:
		return True

def scan_all(path=None):
	conf = readConf()
	dbfile = f"{data_dir}/nplayer.db"
	if path is None:
		series_dir = conf['media_directories']['series']
		music_dir = conf['media_directories']['music']
		movies_dir = conf['media_directories']['movies']
	else:
		series_dir = os.path.join(path, 'series')
		music_dir = os.path.join(path, 'music')
		movies_dir = os.path.join(path, 'movies')
	if os.path.exists(dbfile):
		log("Backing up database...", 'info')
		result = backup_db()
		if result is not True:
			yn = input(f"Warning: database backup encountered an issue: {result}. Continue? (y/n)")
			if yn != 'y':
				log("Aborting...", 'error')
				exit()
	create_db()
	log("Scanning for Movies...", 'info')
	scan_movies(movies_dir)
	log("Scanning for TV Series...", 'info')
	scan_series(series_dir)
	log("Scanning for Music...", 'info')
	scan_music(music_dir)
	log("Done!", 'info')
	yn = input("Run np now? (y/n)")
	if yn == "y":
		subprocess.call('np')
	else:
		log("Exiting...", 'info')
		exit()
	log(f"Running cleandb: All...", 'info')
	cleandb()


if __name__ == "__main__":
	scan_all()
	dbfixer.fix()



