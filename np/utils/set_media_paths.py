from np.core.conf import readConf, writeConf, log
import os

def set_media_paths():
	conf = readConf()
	conf['media_directories'] = {}
	log("Starting interactive directory setup...", 'info')
	media_dirs = None
	media_dirs = input("Enter media storage directory (see readme file in git download folder for details) ")
	if media_dirs is None:
		txt = ("Error: no media directory entered! Aborting...")
		return
	else:
		conf['media_directories'] = {}
		conf['media_directories']['main'] = media_dirs
		music_dir = (media_dirs + os.path.sep + "Music")
		movies_dir = (media_dirs + os.path.sep + "Movies")
		series_dir = (media_dirs + os.path.sep + "Series")
		conf['media_directories']['movies'] = movies_dir
		conf['media_directories']['music'] = music_dir
		conf['media_directories']['series'] = series_dir
		log("Media directories configured! Continuing...", 'info')
	writeConf(conf)
	return conf['media_directories']
