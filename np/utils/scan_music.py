#!/usr/bin/env python3
import np
import subprocess
import eyed3
import os

home = os.path.expanduser("~")
DATA_DIR = (home + os.path.sep + ".np")
totag_file = (DATA_DIR + os.path.sep + "needs_tagged.txt")

def scan_music(target_dir=None):
	np.test_db()
	conf = np.readConf()
	if target_dir == None:
		target_dir = conf['media_directories']['music']
	com = ("find '" + target_dir + "' -name '*.mp3'")
	files = subprocess.check_output(com, shell=True).decode().strip()
	files = files.split("\n")
	needs_tagged = []
	ct = len(files)
	pos = 0
	for filepath in files:
		pos = pos + 1
		data = {}
		txt = ("Progress: (" + str(pos) + "/" + str(ct) + ", filepath:" + filepath)
		print (txt)
		if filepath == '':
			pass
		try:
			audiofile = eyed3.load(filepath)
			if audiofile.tag is not None:
				data['isactive'] = 1
				data['title'] = str(audiofile.tag.title)
				data['album'] = str(audiofile.tag.album)
				data['year'] = str(audiofile.tag.release_date)
				data['artist'] = str(audiofile.tag.artist)
				data['track'] = audiofile.tag.track_num
				data['filepath'] = filepath
			else:
				tag = audiofile.initTag()
				txt = ("scan_music(): No tag found for file:" + filepath)
				np.log(txt, 'error')
				data['isactive'] = 1
				data['artist'] = str(input("Enter artist: "))
				tag.artist = data['artist']
				data['title'] = str(input("Enter title: "))
				tag.title = data['title']
				data['album'] = str(input("Enter album (blank for none): "))
				if data['album'] == '':
					data['album'] = 'null'
				tag.album = data['album']
				data['year'] = str(input("Enter year (blank for none): "))
				if data['year'] == '':
					data['year'] = 'null'
				tag.year = data['year']
				data['track'] = str(input("Enter track (blank for none): "))
				if data['track'] == '':
					data['track'] = 'null'
				tag.track_num = data['track']
				data['filepath'] = filepath
				tag.save()
			ret = np.addtodb_new('music', data)
			if ret is not True:
				print (ret)
		except Exception as e:
			txt = ("Exception in scan_music:" + e + ", filepath=" + filepath)
			np.log(txt, 'error')
			needs_tagged.append(filepath)
	tagct = len(needs_tagged)
	if tagct > 0:
		j = "\n"
		out = j.join(needs_tagged)
		print (tagct, out)
		with open (totag_file, 'w') as f:
			f.write(out)
		f.close()
		txt = ("Music scanner exited with issues! Affected files logged to file:" + totag_file)
		np.log(txt, 'error')
	else:
		np.log("Music scanner completed succesfully!", 'info')
		return "Finished!"


if __name__ == "__main__":
	import sys
	try:
		target_dir = sys.argv[1]
		scan_music(target_dir)
	except:
		scan_music()
