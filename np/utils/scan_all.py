from np import scan_music, scan_movies, scan_series, readConf, DATA_DIR, create_db
import subprocess
import os


def backup_db():
	com = f"cd '{DATA_DIR}'; mv nplayer.db nplayer.db.bak"
	ret = subprocess.check_output(com, shell=True)
	if ret:
		print (ret)
		return ret
	else:
		print ("OK")
		return True

def scan_all():
	dbfile = f"{DATA_DIR}/nplayer.db"
	if os.path.exists(dbfile):
		print ("Backing up database...")
		result = backup_db()
		if result is not True:
			yn = input(f"Warning: database backup encountered an issue: {result}. Continue? (y/n)")
			if yn != 'y':
				print ("Aborting...")
				exit()
	create_db()
	conf = readConf()
	series_dir = conf['media_directories']['series']
	music_dir = conf['media_directories']['music']
	movies_dir = conf['media_directories']['movies']	
	print ("Scanning for TV Series...")
	scan_music(series_dir)
	print ("Scanning for Movies...")
	scan_movies(movies_dir)
	print ("Scanning for Music...")
	scan_music(music_dir)
	print ("Done!")
	yn = input("Run np now? (y/n)")
	if yn == "y":
		subprocess.call('np')
	else:
		print ("Exiting...")
		exit()


if __name__ == "__main__":
	scan_all()




