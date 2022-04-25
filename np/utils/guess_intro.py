#!/usr/bin/env python3
import subprocess
import json

def guess_intro(_file):
	com = ("ffprobe -v quiet -print_format json -show_format -show_streams '" + _file + "'")
	data = subprocess.check_output(com, shell=True).decode().strip()
	json_data = json.loads(data)
	duration = float(json_data['format']['duration'])
	com = ("ffprobe -i '" + _file + "' -print_format json -show_chapters -loglevel error")
	data = subprocess.check_output(com, shell=True).decode().strip()
	json_data = json.loads(data)
	for chapter in json_data['chapters']:
		s = float(chapter['start_time'])
		e = float(chapter['end_time'])
		sp = float(s / duration)
		ep = float(e / duration)
		d = e - s
		if d >= 15 and d <= 50:
			print ("Guessed intro:", sp, ep, d)
			break

if __name__ == "__main__":
	import sys
	_file = sys.argv[1]
	print (guess_chapter(_file))
