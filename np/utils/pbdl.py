import pathlib
import shutil
import requests
import os
import PySimpleGUI as sg
import subprocess
import np
import urllib

def get_permissions():
	ret = subprocess.check_output('sudo chmod -R a+rwx /var/lib/transmission-daemon/downloads', shell=True)
	return ret


class pbdl():
	def __init__(self):
		self.pbdl_save_dir = "/var/lib/transmission-daemon/downloads"
		self.active_torrents = []
		self.conf = np.readConf()
		self.conf['windows'] = {}
		self.conf['windows']['pbdl'] = {}
		self.columns_list = []
		self.files = []
		self.media_info = {}
		self.poster_img_size_w = 300
		self.poster_img_size_h = 300
		self.tid = None
		self.selected_file = None
		ret = get_permissions()
		self.auto_remove = True
		#print ("Get permisssions:", ret)
		self.categories = {}
		self.categories['Audio'] = {}
		self.categories['Audio']['Main'] = 100
		self.categories['Audio']['Music'] = 101
		self.categories['Audio']['Audio books'] = 102
		self.categories['Audio']['Sound clips'] = 103
		self.categories['Audio']['FLAC'] = 104
		self.categories['Audio']['Other'] = 199
		self.categories['Video'] = {}
		self.categories['Video']['Main'] = 200
		self.categories['Video']['Movies'] = 201
		self.categories['Video']['Movies DVDR'] = 202
		self.categories['Video']['Music videos'] = 203
		self.categories['Video']['Movie clips'] = 204
		self.categories['Video']['TV shows'] = 205
		self.categories['Video']['Handheld'] = 206
		self.categories['Video']['HD - Movies'] = 207
		self.categories['Video']['HD - TV shows'] = 208
		self.categories['Video']['3D'] = 209
		self.categories['Video']['Other'] = 299
		self.categories['Applications'] = {}
		self.categories['Applications']['Main'] = 300
		self.categories['Applications']['Windows'] = 301
		self.categories['Applications']['Mac'] = 302
		self.categories['Applications']['UNIX'] = 303
		self.categories['Applications']['Handheld'] = 304
		self.categories['Applications']['IOS (iPad/iPhone)'] = 305
		self.categories['Applications']['Android'] = 306
		self.categories['Applications']['Other OS'] = 399
		self.categories['Games'] = {}
		self.categories['Games']['Main'] = 400
		self.categories['Games']['PC'] = 401
		self.categories['Games']['Mac'] = 402
		self.categories['Games']['PSx'] = 403
		self.categories['Games']['XBOX360'] = 404
		self.categories['Games']['Wii'] = 405
		self.categories['Games']['Handheld'] = 406
		self.categories['Games']['IOS'] = 407
		self.categories['Games']['Android'] = 408
		self.categories['Games']['Other'] = 499
		self.categories['Porn'] = {}
		self.categories['Porn']['Main'] = 500
		self.categories['Porn']['Movies'] = 501
		self.categories['Porn']['Movies DVDR'] = 502
		self.categories['Porn']['Pictures'] = 503
		self.categories['Porn']['Games'] = 504
		self.categories['Porn']['HD - Movies'] = 505
		self.categories['Porn']['Movie clips'] = 506
		self.categories['Porn']['Other'] = 599
		self.categories['Other'] = {}
		self.categories['Other']['Main'] = 600
		self.categories['Other']['E-books'] = 601
		self.categories['Other']['Comics'] = 602
		self.categories['Other']['Pictures'] = 603
		self.categories['Other']['Covers'] = 604
		self.categories['Other']['Physibles'] = 605
		self.categories['Other']['Other'] = 699
		self.categories['All'] = {}
		self.categories['All']['Audio'] = list(self.categories['Audio'].keys())
		self.categories['All']['Video'] = list(self.categories['Video'].keys())
		self.categories['All']['Applications'] = list(self.categories['Applications'].keys())
		self.categories['All']['Games'] = list(self.categories['Games'].keys())
		self.categories['All']['Porn'] = list(self.categories['Porn'].keys())
		self.categories['All']['Other'] = list(self.categories['Other'].keys())
				

	def send_command(self, com):
		ret = subprocess.check_output(com, stderr=subprocess.STDOUT, shell=True).decode().split("\n")
		return ret


	def get_torrents(self):
		data = self.send_command("transmission-remote -l")
		outlist = []
		for line in data:
			outstr = None
			line = line.strip()
			chunks = line.split(" ")
			for chunk in chunks:
				if chunk != '':
					if outstr == None:
						outstr = str(chunk)
					else:
						outstr = (outstr + "|" + str(chunk))
			outlist.append(outstr)
		self.torrent_data = {}
		for line in outlist:
			data = {}
			if line is not None:
				if line.split('|')[0] == 'ID' or line.split('|')[0] == 'Sum:':
					pass
				else:

					chunks = line.split('|')
					tid = chunks[0]
					data['percent'] = chunks[1]
					data['have'] = chunks[2]
					data['size_unit'] = chunks[3]
					data['eta'] = chunks[4]
					data['up'] = chunks[5]
					data['down'] = chunks[6]
					data['ratio'] = chunks[7]
					data['status'] = chunks[8]
					length = len(chunks)
					name_pieces = chunks[9:length]
					j = ' '
					data['name'] = j.join(name_pieces)
					string = (str(tid) + ":" + str(data['name']) + "|" + str(data['percent']))
					self.active_torrents.append(string)
					self.torrent_data[tid] = data
		self.pbdl_win['-TORRENT_SELECT-'].update(self.active_torrents)
		return self.torrent_data


	def get_files(self, tid):
		string = ("transmission-remote -t" + str(tid) + " --files")
		data = self.send_command(string)
		pos = -1
		self.files = []
		for line in data:
			pos = pos + 1
			if pos >= 0:
				if 'GB ' in line:
					_file = line.split('GB ')[1].strip()
					self.files.append(_file)
				elif 'MB ' in line:
					_file = line.split('MB ')[1].strip()
					self.files.append(_file)
				elif 'KB ' in line:
					_file = line.split('KB ')[1].strip()
					self.files.append(_file)
				else:
					pass
		self.pbdl_win['-TORRENT_FILES-'].update(self.files)
		return self.files

		



	def create_window(self):
		self.play_type = self.conf['play_type']
		self.menu_def = [['&File', ['E&xit']], ['&Toolbar', ['&Remove Torrent', '&Delete Torrent', '&Query TMDB', 'VPN', ['&0 Off', '&1 On', '&2 Status']]], ['&Help', '&About...']]
		if self.play_type == 'movies':
			self.columns_list = ['title', 'tmdbid', 'year', 'release_date', 'duration', 'description', 'poster', 'filepath', 'md5', 'url']
		elif self.play_type == 'series' or self.play_type == 'videos':
			self.columns_list = ['series_name', 'tmdbid', 'season', 'episode_number', 'episode_name', 'description', 'air_date', 'still_path', 'duration', 'filepath', 'md5', 'url']
		elif self.play_type == 'music':
			self.columns_list = ['title', 'accoustic_id', 'album', 'album_id', 'artist_id', 'year', 'artist', 'track', 'track_ct', 'filepath']
		poster_path = (np.npdir + os.path.sep + 'poster.png')

		self.pbdl_layout = [
		[sg.Listbox(self.active_torrents, expand_x=True, enable_events=True, size=(50,10), key='-TORRENT_SELECT-')],
		[sg.Text('TID:'), sg.Text('', expand_x=True, key='-TID-')],
		[sg.Text('Name:'), sg.Text('', expand_x=True, key='-Name-')],
		[sg.Text('Percent:'), sg.Text('', expand_x=True, key='-Percent-')],
		[sg.Text('Have:'), sg.Text('', expand_x=True, key='-Have-')],
		[sg.Text('ETA:'), sg.Text('', expand_x=True, key='-ETA-')],
		[sg.Text('Upload Rate:'), sg.Text('', expand_x=True, key='-Upload Rate-')],
		[sg.Text('Download Rate:'), sg.Text('', expand_x=True, key='-Download Rate-')],
		[sg.Text('Status:'), sg.Text('', expand_x=True, key='-Status-')],
		[sg.Text('Ratio:'), sg.Text('', expand_x=True, key='-Ratio-')],
		[sg.Listbox(self.files, expand_x=True, enable_events=True, select_mode='multiple', size=(50,10), key='-TORRENT_FILES-')]

	]
		self.title_bar_layout = [sg.MenubarCustom(self.menu_def, tearoff=False, key='-menubar_key-'), sg.Combo(['series', 'movies', 'music'], self.conf['play_type'] , enable_events=True,key='-MEDIA_TYPE-'), sg.Button("Close", key='-Close PBDL-')],
		self.title_bar_frame = sg.Frame(title='', layout = self.title_bar_layout, key='title_bar_frame', expand_x=True, grab=True, element_justification="center", vertical_alignment="top")
		self.poster_url = 'http://192.168.2.2/NicoleLogo.png'
		response = requests.get(self.poster_url, stream=True)
		response.raw.decode_content = True
		img = response.raw.read()
		self.imgfile = 'poster.png'
		with open(self.imgfile, 'wb') as f:
			f.write(img)
		self.resize_img(self.imgfile)
		self.poster_layout = [[sg.Image(self.imgfile, key='-POSTER_PNG-')]]
		self.media_info_layout = []
		is_active_ckbox = [sg.Checkbox(text='Is Active:', auto_size_text=True, change_submits=True, enable_events=True, key='-SET_ACTIVE-'), sg.Checkbox(text='Auto Remove Torrents:', auto_size_text=True, change_submits=True, enable_events=True, key='-AUTO_REMOVE-')]
		self.media_info_layout.append(is_active_ckbox)
		pos = -1
		for column in self.columns_list:
			pos = pos + 1
			d = ("d_" + str(pos))
			k = ("-" + str(pos) + "-")
			line = [sg.Text(column, key=d), sg.Input(default_text='', enable_events=True, do_not_clear=True, key=k, expand_x=True)]
			self.media_info_layout.append(line)
		media_info_actions = [sg.Button('Query TMDB', key='-Query TMDB-'), sg.Button('Migrate Files', key='-Migrate Files-'), sg.Button('Read from database', '-Read from database-'), sg.Button('Remove'), sg.Button('Remove+Delete'), sg.Button('Exclude')]
		self.media_info_layout.append(media_info_actions)
		
		# build frames
		info_frame = sg.Frame(title='Torrent Data', layout=self.pbdl_layout, key='info_frame', expand_x=True, grab=True, element_justification="left", vertical_alignment="top")
		poster_frame = sg.Frame(title='Poster Data', layout=self.poster_layout, key='poster_frame', expand_x=True, grab=True, element_justification="center", vertical_alignment="center")
		media_info_frame = sg.Frame(title='Media Info', layout=self.media_info_layout, key='media_info_frame', expand_x=True, grab=True, element_justification="right", vertical_alignment="top")
		self.layout = [[self.title_bar_frame], [info_frame, poster_frame, [media_info_frame]], [sg.Sizegrip(key='-gui_size-')]]
		
		#get sizes
		try:
			x = int(self.conf['windows']['pbdl']['x'])
			y = int(self.conf['windows']['pbdl']['y'])
			w = int(self.conf['windows']['pbdl']['w'])
			h = int(self.conf['windows']['pbdl']['h'])
		except:
			self.conf['windows'] = np.init_window_position()
			x = int(self.conf['windows']['pbdl']['x'])
			y = int(self.conf['windows']['pbdl']['y'])
			w = int(self.conf['windows']['pbdl']['w'])
			h = int(self.conf['windows']['pbdl']['h'])
		self.pbdl_win = sg.Window('GUI', self.layout, no_titlebar=True, location=(x,y), size=(w,h), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()


	def remove_torrent(self, tid):
		com = ("transmission-remote -t" + str(tid) + " -rad")
		ret = self.send_command(com)
		self.get_torrents()
		return ret


	def get_poster(self, poster_url):
		try:
			self.poster_url = poster_url
			self.imgfile = 'poster.png'
			response = requests.get(self.poster_url, stream=True)
			response.raw.decode_content = True
			img = response.raw.read()
			with open(self.imgfile, 'wb') as f:
				f.write(img)
			f.close()
			#TODO: insert image resize here
			self.resize_img(self.imgfile)
			self.pbdl_win['-POSTER_PNG-'].update(self.imgfile)
			self.pbdl_win.refresh()
		except Exception as e:
			print ("Unable to deal with poster url...", poster_url)


	def resize_img(self, img, w=None, h=None):
		if w is None and h is None:
			size = (str(self.poster_img_size_w) + "x" + str(self.poster_img_size_h))
		comstr = ("convert " + str(img) + " -resize " + str(size) + " poster.png")
		ret = self.send_command(comstr)


	def lookup(self, _files=None):
		if _files is None:
			if self.selected_file is None:
				self.selected_file = self.get_files(self.tid)
		else:
			self.selected_file = _files
		global uivalues, uievent
		self.add_to_db_data = []
		if self.conf['play_type'] == 'series':
			if type(self.selected_file) != list:
				self.selected_file = [self.selected_file]
			for item in self.selected_file:
				if item is not None:
					self.sourcePath = ('/var/lib/transmission-daemon/downloads' + os.path.sep + item)
					try:
						self.sinfo, self.season, self.episode_number = np.seinfo(item)
					except:
						self.season = self.media_info['season']
						self.episode_number = self.media_info['episode_number']
						self.sinfo = ('S' + str(self.season) + 'E' + str(self.episode_number))
					sidx = ("-" + str(self.columns_list.index('season')) + "-")
					eidx = ("-" + str(self.columns_list.index('episode_number')) + "-")
					nidx = ("-" + str(self.columns_list.index('series_name')) + "-")
					self.series_name = self.values[nidx]
					if "'" in self.series_name:
						chunks = self.series_name.split("'")
						j = "_"
						self.series_name = j.join(chunks)
					print (self.series_name)
					self.pbdl_win[sidx].update(self.season)
					self.pbdl_win[eidx].update(self.episode_number)
					print (self.series_name, self.sinfo, self.season, self.episode_number)
					test1 = ("." + self.sinfo)
					test2 = self.sinfo
					test3 = " Season"
					test4 = "("
					test5 = ")"
					test6 = " ("
					test7 = ".("
					splitter = None
					if test1 in self.series_name or test2 in self.series_name or test3 in self.series_name or test4 in self.series_name or test5 in self.series_name or test6 in self.series_name or test7 in self.series_name:
						if test1 in self.series_name:
							self.series_name = self.series_name.split(test1)[0]
						if self.sinfo in self.selected_file:
							self.series_name = self.series_name.split(test2)[0]
						if " Season" in self.selected_file:
							self.series_name = self.series_name.split(test3)[0]
						if " (" in self.series_name:
							self.series_name = self.series_name.split(test4)[0]
						if ".(" in self.series_name:
							self.series_name = self.series_name.split(test5)[0]
						if "(" in self.series_name:
							self.series_name = self.series_name.split(test6)[0]
						if '.' in self.series_name:
							j = ' '
							self.series_name = j.join(self.series_name.split('.'))
					self.pbdl_win['-0-'].update(self.series_name)
					print ("Querying:", self.series_name, self.season, self.episode_number)
					ret = np.query_series(self.series_name, self.season, self.episode_number)
					print ("Series lookup results:", ret)
					if not ret:
						print ("Series lookup failed for ", self.series_name, self.season, self.episode_number)
						pass
					else:
						self.add_series(ret)
	def add_series(self, series_data):
		self.air_date = series_data['air_date']
		self.episode_name = series_data['name']
		if "'" in self.episode_name:
			chunks = self.episode_name.split("'")
			j = "_"
			self.episode_name = j.join(chunks)
		self.description = series_data['overview']
		if "'" in self.description:
			try:
				j = '_'
				pieces = self.description.split("'")
				self.description = j.join(pieces)
			except:
				self.description = urllib.parse.quote(self.description)
		self.tmdbid = series_data['id']
		self.still_path = str(series_data['still_path'])
		poster = ("https://image.tmdb.org/t/p/original" + self.still_path)
		self.get_poster(poster)
		self.media_type = 'series'
		extlen = len(self.sourcePath.split('.')) - 1
		ext = str(self.sourcePath.split('.')[extlen])
		fname = (self.series_name + ".S" + str(self.season) + "E" + str(self.episode_number) + "." + str(self.episode_name) + "." + ext)
		newdir = ('/var/storage/Series' + os.path.sep + self.series_name + os.path.sep + "S" + str(self.season))
		pathlib.Path(newdir).mkdir(parents=True, exist_ok=True)
		self.destinationPath = (newdir + os.path.sep + fname)
		self.insert_query_string = ("INSERT INTO series (isactive, series_name, tmdbid, season, episode_number, episode_name, description, air_date, still_path, duration, filepath, md5, url) VALUES(1, '" + str(self.series_name) + "', '" + str(self.tmdbid) + "', '" + str(self.season) + "', '" + str(self.episode_number) + "', '" + str(self.episode_name) + "', '" + str(self.description) + "', '" + str(self.air_date) + "', '" + str(self.still_path) + "', 'None', '" + str(self.destinationPath) + "', 'None', 'None');")
		ret = self.add_to_db(self.insert_query_string)
		if ret:
			print (ret)



	def add_to_db(self, insert_query_string=None):
		if insert_query_string is not None:
			self.insert_query_string = insert_query_string
		ret = np.addtodb(self.conf['play_type'], self.insert_query_string)
		try:
			shutil.move(self.sourcePath, self.destinationPath)
			return True
		except Exception as e:
			self.auto_remove = False
			print ("line 294, pbdl.py", e)
			return False



	def run(self):
		while True:
			self.event, self.values = self.pbdl_win.read(timeout=10)
			if self.event == sg.WIN_CLOSED or self.event=='-Close PBDL-' or self.event == "Exit":
				if self.event == '-Close PBDL-':
					self.pbdl_win.close()
				break
			else:
				if self.event != '__TIMEOUT__':
					if self.event == '-TORRENT_SELECT-':
						self.tid = self.values[self.event][0]
						self.tid = self.tid.split(':')[0]
						self.pbdl_win['-TID-'].update(self.tid)
						self.pbdl_win['-Name-'].update(self.torrent_data[self.tid]['name'])
						self.pbdl_win['-0-'].update(self.torrent_data[self.tid]['name'])
						self.pbdl_win['-Percent-'].update(self.torrent_data[self.tid]['percent'])
						string = (str(self.torrent_data[self.tid]['have']) + " " + str(self.torrent_data[self.tid]['size_unit']))
						self.pbdl_win['-Have-'].update(string)
						self.pbdl_win['-ETA-'].update(self.torrent_data[self.tid]['eta'])
						self.pbdl_win['-Upload Rate-'].update(self.torrent_data[self.tid]['up'])
						self.pbdl_win['-Download Rate-'].update(self.torrent_data[self.tid]['down'])
						self.pbdl_win['-Status-'].update(self.torrent_data[self.tid]['status'])
						self.pbdl_win['-Ratio-'].update(self.torrent_data[self.tid]['ratio'])
						self.torrent_data[self.tid]['files'] = self.get_files(self.tid)
					elif self.event == '-Migrate Files-':
						if self.selected_file is None:
							self.selected_file = self.get_files(self.tid)
						self.lookup()

					elif self.event == '-AUTO_REMOVE-':
						if self.auto_remove == True:
							self.auto_remove = False
						else:
							self.auto_remove = True
						print ("Auto Remove set to ", self.auto_remove)
					elif self.event == '-TORRENT_FILES-':
						#try:
						self.selected_file = self.values[self.event]
						print ("Selected files:", self.selected_file)
					elif self.event == 'Remove':
						if self.tid is None:
							print ("Select a torrent file first!")
						else:
							self.remove_torrent(self.tid)
							print ("Torrent removed:", self.tid)
							
					elif self.event == '-MEDIA_TYPE-':
						self.play_type = str(self.values[self.event])
						if self.play_type == 'movies':
							self.columns_list = ['title', 'tmdbid', 'year', 'release_date', 'duration', 'description', 'poster', 'filepath', 'md5', 'url']
						elif self.play_type == 'series' or self.play_type == 'videos':
							self.columns_list = ['series_name', 'tmdbid', 'season', 'episode_number', 'episode_name', 'description', 'air_date', 'still_path', 'duration', 'filepath', 'md5', 'url']
						elif self.play_type == 'music':
							self.columns_list = ['title', 'accoustic_id', 'album', 'album_id', 'artist_id', 'year', 'artist', 'track', 'track_ct', 'filepath']
						pos = -1
						for column in self.columns_list:
							pos = str(int(pos) + 1)
							d = ("d_" + pos)
							self.pbdl_win[d].update(column)
						self.pbdl_win.refresh()
						
					elif self.event == '-0-' or self.event == '-1-' or self.event == '-2-' or self.event == '-3-' or self.event == '-4-' or self.event == '-5-' or self.event == '-6-' or self.event == '-7-' or self.event == '-8-' or self.event == '-9-' or self.event == '-10-':
						try:
							val = self.values[self.event]
							pos = int(self.event.split('-')[1])
							column = self.columns_list[pos]
							if "'" in val:
								chunks = val.split("'")
								j = "_"
								val = j.join(chunks)
							self.media_info[column] = val
							self.id = self.values[self.event][0]
						except:
							pass
					elif self.event == '-Query TMDB-':
						if self.play_type == 'series':
							self.lookup()
					else:
						#pass
						print (self.event, self.values)

if __name__ == "__main__":
	pbdl = pbdl()
	pbdl.create_window()
	pbdl.get_torrents()
	pbdl.run()
