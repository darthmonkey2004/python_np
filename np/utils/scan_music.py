#!/usr/bin/env python3
import np
import subprocess
import eyed3

def scan_music(target_dir=None):
	conf = np.readConf()
	if target_dir == None:
		target_dir = conf['media_directories']['music']
	com = ("find '" + target_dir + "' -name '*.mp3'")
	files = subprocess.check_output(com, shell=True).decode()
	files = files.split("\n")
	needs_tagged = []
	for filepath in files:
		print ("filepath", filepath)
		try:
			audiofile = eyed3.load(filepath)
			if audiofile.tag is not None:
				data = {}
				data['isactive'] = 1
				data['title'] = str(audiofile.tag.title)
				data['album'] = str(audiofile.tag.album)
				data['year'] = str(audiofile.tag.release_date)
				data['artist'] = str(audiofile.tag.artist)
				data['track'] = audiofile.tag.track_num
				data['filepath'] = filepath
				ret = np.addtodb_new('music', data)
				if ret:
					print (ret)
			else:
				needs_tagged.append(filepath)
		except:
			needs_tagged.append(filepath)
	if len(needs_tagged) >= 0:
		j = "\n"
		out = j.join(needs_tagged)
		with open ("needs_tagged.txt", 'w') as f:
			f.write(out)
		f.close()

if __name__ == "__main__":
	import sys
	try:
		target_dir = sys.argv[1]
		scan_music(target_dir)
	except:
		scan_music()
