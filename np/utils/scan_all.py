from np.utils.scan_music import scan_music
from np.utils.scan_movies import scan_movies
from np.utils.scan_series import scan_series
from np.core.conf import readConf
from np.core.nplayer_db import create_db
import subprocess
import os
import datetime
data_dir = os.path.join(os.path.expanduser("~"), '.np')

def backup_db():
	ts = datetime.datetime.now().timestamp()
	newname = (f"{ts}.nplayer.backup.db")
	com = f"cd '{data_dir}'; mv nplayer.db {newname}"
	ret = subprocess.check_output(com, shell=True)
	if ret:
		return ret
	else:
		return True

def scan_all(dir=None):
	conf = readConf()
	dbfile = f"{data_dir}/nplayer.db"
	if dir == None:
		series_dir = conf['media_directories']['series']
		music_dir = conf['media_directories']['music']
		movies_dir = conf['media_directories']['movies']
	else:
		series_dir = (f"{dir}{os.path.sep}series")
		music_dir = (f"{dir}{os.path.sep}music")
		movies_dir = (f"{dir}{os.path.sep}movies")
	if os.path.exists(dbfile):
		np.log("Backing up database...", 'info')
		result = backup_db()
		if result is not True:
			yn = input(f"Warning: database backup encountered an issue: {result}. Continue? (y/n)")
			if yn != 'y':
				np.log("Aborting...", 'error')
				exit()
	create_db()
	log("Scanning for Music...", 'info')
	scan_music(music_dir)
	log("Scanning for Movies...", 'info')
	scan_movies(movies_dir)
	log("Scanning for TV Series...", 'info')
	scan_series(series_dir)
	log("Done!", 'info')
	yn = input("Run np now? (y/n)")
	if yn == "y":
		subprocess.call('np')
	else:
		log("Exiting...", 'info')
		exit()
	np.log(f"Running cleandb: All...", 'info')
	np.cleandb()


if __name__ == "__main__":
	scan_all()




