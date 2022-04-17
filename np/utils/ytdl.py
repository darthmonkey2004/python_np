#!/usr/bin/env python3

import threading
import subprocess
import sys
import io
import youtube_dl
import np
import PySimpleGUI as sg


class logger(object):
	def debug(self, msg):
		pass
	def warning(self, msg):
		pass
	def error(self, msg):
		print(msg)


class ytdl():
	def __init__(self):
		self.conf = np.readConf()
		windows = np.init_window_position()
		self.x = windows['ytdl']['x']
		self.y = windows['ytdl']['y']
		self.w = windows['ytdl']['w']
		self.h = windows['ytdl']['h']
		self.search_results = []
		self.window = None
		self.event = None
		self.values = None
		self.target_url = None
		self.media_type = 'audio'
		self.sim_opts = {'simulate': True}
		self.ytdl_infogetter = youtube_dl.YoutubeDL(self.sim_opts)

	def init_ytdl_gui(self):
		url_line = [sg.Text('Target URL:'), sg.Input(expand_x=True, enable_events=True, key='-YTDL_TARGET_URL-')]
		#results_section = [sg.Listbox(self.search_results, key='-YTDL_SEARCH_RESULTS-', size=(100,10), expand_y=True, enable_events=True)]
		#output_section = [sg.Multiline(autoscroll=True, change_submits=True, enable_events=True, auto_refresh=True, reroute_stdout=True, reroute_stderr=True, reroute_cprint=True, key='-OUTPUT-', size=(100,10), expand_x=True)]
		media_types=['video', 'audio']
		picker_media_types = sg.Combo(media_types,default_value=self.media_type,enable_events=True,key='-SET_MEDIA_TYPE-')
		submit_controls = [picker_media_types, sg.Button('Download', key='-YTDL_DOWLOAD-'), sg.Button('Close', key='-YTDL_CLOSE-')]
		progress_bar = [sg.ProgressBar(max_value=10, orientation='h', size=(20, 20), expand_x=True, key='progress')]
		self.layout = [
			[url_line],
			[progress_bar],
			#[output_section],
			[submit_controls]
		]
		self.win = sg.Window('YTDL_WINDOW', self.layout, location=(int(self.x),int(self.y)), size=(int(self.w),int(self.h)), keep_on_top=False, element_justification='center', finalize=True, resizable=True).Finalize()
		return self.win


	def get_event(self):
		self.window, self.event, self.values = sg.read_all_windows(timeout=10)

		return (self.window, self.event, self.values)


	def get_info(self, url):
		self.info = self.ytdl_infogetter.extract_info(url)
		return self.info

	def download(self, url, _type='video'):
		ytdl_downloader = None
		info = self.get_info(url)
		_id = info['id']
		ext = info['ext']
		if _type == 'video':
			outtmpl = "{_id}.{ext}".format(_id=_id, ext=ext)
			dl_opts = {'outtmpl': outtmpl, 'logger': logger(), 'progress_hooks': [progress_hook]}
			ytdl_downloader = youtube_dl.YoutubeDL(dl_opts)

		elif _type == 'audio':
			try:
				title = info['title']
				artist = info['artist']
				outtmpl = (title + "." + artist + "." + ext)
				dl_opts = {'outtmpl': outtmpl, 'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 'logger': logger(), 'progress_hooks': [progress_hook]}
			except:
				outtmpl = (_id + "." + ext)
				dl_opts = {'outtmpl': outtmpl, 'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 'logger': logger(), 'progress_hooks': [progress_hook]}
			ytdl_downloader = youtube_dl.YoutubeDL(dl_opts)
		ytdl_downloader.download([url])


	def start(self):
		win = self.init_ytdl_gui()
		while True:
			try:
				data = self.get_event()
			except Exception as e:
				data = None
				print ("ytdl.py, line 101, Event read exception:", e)
			if data is not None:
				w, e, v = data
				if e == sg.WIN_CLOSED or e == '-YTDL_EXIT-' or e == '-YTDL_CLOSE-':
					break
				elif e == '-YTDL_TARGET_URL-':
					self.target_url = str(v[e])
					np.write_log(("Target Url:", self.target_url), 'INFO')
				elif e == '-YTDL_DOWLOAD-':
					u = self.target_url
					if u is not None:
						ret = downloader(u, self.media_type)
						print (u, ret)
					else:
						print ("No url provided!")
				elif e == '-SET_MEDIA_TYPE-':
					self.media_type = v[e]
					print ("Set media type:", self.media_type)
				else:
					if e != '__TIMEOUT__':
						try:
							print ("Event loop output:", e, v[e])
						except:
							print ("Event loop output:", e)


def downloader(url, _type='video'):
	def worker():
		return Y.download(url, _type)

	thread = threading.Thread(target=worker, daemon=True)
	thread.start()
	

def progress_hook(d):
	if d['status'] == 'finished':
		p = 0
	try:
		p = d['_percent_str'].split('%')[0].strip()
		p = float(p)
	except:
		p = 100
	win['progress'].update_bar(p)


if __name__ == "__main__":
	Y = ytdl()
	win = Y.init_ytdl_gui()
	Y.start()
