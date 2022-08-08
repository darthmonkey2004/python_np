from os.path import basename
import np
import subprocess


def scan_series(target_dir=None):
	exts = ['mp4', 'mov', 'avi', 'flv']
	np.test_db()
	conf = np.readConf()
	if target_dir == None:
		target_dir = conf['media_directories']['music']
	for ext in exts:
		com = (f"find '{target_dir}' -name '*.{ext}'")
		files = subprocess.check_output(com, shell=True).decode().strip()
		files = files.split("\n")
		for filepath in files:
			fname = basename(filepath)
			try:
				series_name = fname.split('.')[0]
				sinfo = fname.split('.')[1]
				season = int(sinfo.split('E')[0].split('S')[1])
				episode_number = int(sinfo.split('E')[1])

			except Exception as e:
				print (f"Exception: {e}")
				print (f"Filepath: {filepath}")
				series_name = input ("Enter series name: ")
				season = input ("Enter season number: ")
				episode_number = input ("Enter episode number: ")
			
			
			ret = np.add_series(filepath, series_name, season, episode_number)
			if ret == False:
				print (ret)
				input()
			else:
				print ("OK!")

if __name__ == "__main__":
	import sys
	target_dir = sys.argv[1]
	scan_music(target_dir)
