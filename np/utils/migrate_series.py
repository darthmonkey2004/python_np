import shutil
import urllib
import pathlib
import np
pbdl = np.pbdl()

def migrate_season(tid, series_name, season):
	pbdl.play_type = 'series'
	pos = 0
	files = pbdl.get_files(int(tid))
	for filepath in files:
		pos = pos + 1
		episode_number = pos
		info = np.query_series(series_name, season, episode_number)
		filepath = urllib.parse.unquote(filepath)
		extlen = len(filepath.split('.')) - 1
		ext = str(filepath.split('.')[extlen])
		srcpath = ('/var/lib/transmission-daemon/downloads/' + filepath)
		episode_name = info['episode_name']
		if episode_name == 'null' or episode_name is None:
			fname = (series_name + ".S" + str(season) + "E" + str(episode_number) + "." + ext)
		else:
			fname = (series_name + ".S" + str(season) + "E" + str(episode_number) + "." + episode_name + "." + ext)
		destdir = ('/var/storage/Series/' + series_name + "/S" + str(season))
		pathlib.Path(destdir).mkdir(parents=True, exist_ok=True)
		destpath = (destdir + "/" + fname)
		info['filepath'] = destpath
		ret = np.add_to_db('series', info)
		if ret is not True:
			print (ret)
		else:
			print ("Added to database. Migrating...:", srcpath, destpath)
			try:
				ret = shutil.move(srcpath, destpath)
				if not ret or ret is None:
					print ("Failed! Aborting...")
					break
				else:
					print ("Migration sucessful!")
					com = ('transmission-remote -t' + str(tid) + " -rad")
					print ("Command:", com)
					input("Press a key to remove torrent!")
					subprocess.check_output(com, shell=True)
				print ("Ok! File added:", filepath)
			except Exception as e:
				print ("Migration failed!:", e)


if __name__ == "__main__":
	import sys
	try:
		tid = sys.argv[1]
		series_name = sys.argv[2]
		season = sys.argv[3]
	except:
		input("Enter torrent id: ")
	ret = migrate_season(tid, series_name, season)
	if ret:
		print (ret)
