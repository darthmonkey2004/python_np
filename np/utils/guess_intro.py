#!/usr/bin/env python3
import subprocess
import json
from np import log

def guess_intro(_file):
	log(f"Guessing intro for file: '{_file}'...", 'info')
	com = (f"ffprobe -v quiet -print_format json -show_format -show_streams \"{_file}\"")
	try:
		data = subprocess.check_output(com, shell=True).decode().strip()
	except:
		return None
	json_data = json.loads(data)
	duration = float(json_data['format']['duration'])
	com = (f"ffprobe -i '{_file}' -print_format json -show_chapters -loglevel error")
	data = subprocess.check_output(com, shell=True).decode().strip()
	json_data = json.loads(data)
	intro = None
	if json_data['chapters'] == []:
		intro = None
		log(f"No chapters available for '{_file}'. Intro = None.", 'info')
		return intro
	else:
		log(f"Chapters found: {json_data['chapters']}", 'info')
		for chapter in json_data['chapters']:
			s = float(chapter['start_time'])
			e = float(chapter['end_time'])
			d = e - s
			
			log(f"Start: {s}, End: {e}, Duration: {d}", 'info')
			if d >= 15 and d <= 60:
				intro_start = ((s / duration) * 100)
				intro_end = ((e / duration) * 100)
				intro = (intro_start, intro_end)
				break
		if intro is not None:
			log(f"Guessed intro:{intro}", 'info')
		else:
			log(f"Chapters out of range (>=15 and d<=60), returning None.", 'info')
		return intro

if __name__ == "__main__":
	import sys
	_file = sys.argv[1]
	print (guess_intro(_file))
