import pickle# be sure to remove this and the pickle dump at the end of build_torrents(), line 168
from np.core.nplayer_db import get_columns
import tmdbsimple as tmdb
import pathlib
import shutil
import requests
import os
import PySimpleGUI as sg
import subprocess
import np
import urllib
import json
from urllib.parse import unquote, quote
from datetime import datetime
conf = np.readConf()
tmdb.API_KEY = 'ac1bdc4046a5e71ef8aa0d0bd93f8e9b'
search = tmdb.Search()
log = np.log


def save_torrent_log(torrents):
	np.log(f"Saving current data!", 'info')
	try:
		with open("torrents.log", "wb") as f:
			pickle.dump(torrents, f)
		f.close()
		if conf['debug'] == True:
			np.log(f"Torrent log updated: {torrents.keys()}", 'info')
		return True
	except Exception as e:
		np.log(f"Error: Unable to write torrent log {e}: data: {torrents}", 'error')
		return False


def get_user_input(window_title='User Input'):
	input_box = sg.Input(default_text='', enable_events=True, change_submits=True, do_not_clear=True, key='-USER_INPUT-', expand_x=True)
	input_btn = sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-OK-')
	layout = [[input_box], [input_btn]]
	input_window = sg.Window(window_title, layout, keep_on_top=False, element_justification='center', finalize=True)
	while True:
		event, values = input_window.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-OK-':
			input_window.close()
		elif event == '-USER_INPUT-':
			user_input = values[event]
	return user_input

def ssh_get_abspath(filepath):
	abspath = None
	remote_dir = "/var/lib/transmission-daemon/downloads"
	fname = os.path.basename(filepath)
	if conf['ssh']['connection_string'] == None:
		ssh_string = get_user_input("Please enter an ssh connection string: (user@host)")
	else:
		ssh_string = conf['ssh']['connection_string']
	try:
		com = (f"cd {np.DATA_DIR}/sftp; find -type f")
		files = subprocess.check_output(com, shell=True).decode().strip().split("\n")
		for _file in files:
			if fname in _file:
				abspath = _file
				return abspath
	except:
		try:
			com = (f"sshfs {ssh_string}:{remote_dir} {np.DATA_DIR}{os.path.sep}sftp")
			ret = subprocess.check_output(com, shell=True).decode().strip()
			com = (f"cd {np.DATA_DIR}/sftp; find -type f")
			files = subprocess.check_output(com, shell=True).decode().strip().split("\n")
			for _file in files:
				if fname in _file:
					abspath = _file
					return abspath
		except Exception as e:
			np.log("Failed to mount sftp! {e}", 'error')
			return None

def send_command(com):
	try:
		ret = subprocess.check_output(com, stderr=subprocess.STDOUT, shell=True).decode().split("\n")
		if ret is not None:
			return ret
		else:
			return True
	except Exception as e:
		log(f"Command failed:{e}, Command: {com}", 'error')
		return False




def test_media_type(filepath):
	filepath = filepath
	sinfo = None
	season = None
	episode_number = None
	try:
		sinfo, season, episode_number = np.seinfo(filepath)
		play_type = 'series'
		length = len(filepath.split(sinfo)) - 1
		series_name = filepath.split(sinfo)[0]
		if '/' in series_name:
			series_name = series_name.split('/')[1]
			out = ('series', [series_name, sinfo, season, episode_number])
			return out
	except Exception as e:
		play_type = 'movies'
		out = None
		if '(' in filepath and ')' in filepath:
			year = int(filepath.split('(')[1].split(')')[0])
			if year >= 1900:
				title = filepath.split(f"({year})")[0].strip()
				return play_type, year, title
		else:
			temp = filepath.split('.')
			if len(temp) > 2:
				title = filepath
			else:
				title = filepath.split('.')[0]
			return 'movies', title, 'Unknown'


def get_torrents():
	np.log("Retreiving torrent data.", 'info')
	torrents = {}
	com = (f"transmission-remote {conf['pbdl_url']} -l")
	data = subprocess.check_output(com, shell=True).decode().strip().split('\n')
	outlist = []
	pos = -1
	for line in data:
		pos += 1
		outstr = None
		if pos > 0:
			line = line.strip()
			chunks = line.split(" ")
			for chunk in chunks:
				if chunk != '':
					if outstr == None:
						outstr = str(chunk)
					else:
						outstr = (outstr + "|" + str(chunk))
			outlist.append(outstr)
	for line in outlist:
		data = {}
		if line is not None:
			if line.split('|')[0] == 'ID' or line.split('|')[0] == 'Sum:':
				pass
			else:
				chunks = line.split('|')
				_id = chunks[0]
				if '*' in _id:
					_id = int(_id.split('*')[0])
				else:
					_id = int(_id)
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
				string = (str(_id) + ":" + str(data['name']) + "|" + str(data['percent']))
				#if string not in active_torrents:
				#	active_torrents.append(string)
				torrents[_id] = data
	#try:
		#pbdl_win['-TORRENT_SELECT-'].update(active_torrents)
	#except:
	#	pass
	return torrents

def build_torrents():
	np.log("Building torrents list (DATA REFRESH)...", 'info')
	ct = 0
	ts = get_torrents()
	_id = 0
	data = {}
	for tid, tinfo in zip(ts.keys(), ts.values()):
		name = tinfo['name']
		com = (f"transmission-remote 192.168.2.2 -t{_id} -f | grep '100%' | grep -v \".jpg\" | grep -v \"sample\" | grep -v \".srt\" | grep -v \".nfo\" | grep -v \".txt\" | cut -d \"/\" -f 2")
		tdata = send_command(com)
		for filepath in tdata:

			_id += 1
			data[_id] = {}
			data[_id]['tid'] = tid
			data[_id]['percent'] = tinfo['percent']
			data[_id]['have'] = tinfo['have']
			data[_id]['size_unit'] = tinfo['size_unit']
			data[_id]['name'] = name
			data[_id]['eta'] = tinfo['eta']
			data[_id]['up'] = tinfo['up']
			data[_id]['down'] = tinfo['down']
			data[_id]['ratio'] = tinfo['ratio']
			data[_id]['status'] = tinfo['status']
			data[_id]['filepath'] = filepath
			data[_id]['tmdbid'] = 'Unknown'
			data[_id]['release_date'] = 'Unknown'
			data[_id]['duration'] = 'Unknown'
			data[_id]['description'] = 'Unknown'
			data[_id]['poster'] = 'Unknown'
			data[_id]['md5'] = 'Unknown'
			data[_id]['url'] = 'Unknown'
			test_ret = test_media_type(name)
			if test_ret is not None:
				data[_id]['play_type'] = test_ret[0]
				data[_id]['title'] = test_ret[1]
				data[_id]['year'] = test_ret[2]
			else:
				data[_id]['play_type'] = None
				data[_id]['title'] = name
				data[_id]['year'] = None
			table = data[_id]['play_type']
			if table == 'series':
				series_name, sinfo, season, episode_number = fileinfo
				pragma = get_columns(table)
				columns = list(pragma.keys())
				data[_id]['sinfo'] = sinfo
				for key in columns:
					if key == 'series_name':
						data[_id]['series_name'] = torrents[_id]['files']['name']
					elif key == 'season':
						data[_id]['season'] = season
					elif key == 'episode_number':
						data[_id]['episode_number'] = episode_number
					elif key == 'filepath':
						data[_id]['filepath'] = torrents[_id]['files']['filepath']
					elif key == 'isactive':
						data[_id]['isactive'] = 1
					else:
						#data[_id][key] = None
						pass
			elif table == 'movies':
				pragma = get_columns(table)
				columns = list(pragma.keys())
				if data[_id]['title'] is None:
					data[_id]['title'] = name
				filepath = data[_id]['filepath']
				if filepath is not None:
					fullpath = ssh_get_abspath(filepath)[1:]
					fullpath = (f"/var/lib/transmission-daemon/downloads/{fullpath}")
				if data[_id]['year'] is None:
					data[_id]['year'] = None
				data[_id]['isactive'] = 1
		print (_id, data[_id])
	return data
	


def load_saved_data():
	bakdata = {}
	np.log("Restoring backup...")
	if os.path.exists("torrents.log"):
		with open("torrents.log", "rb") as f:
			bakdata = pickle.load(f)
		f.close()
	np.log("Backup restored!", 'info')
	return bakdata


def get_permissions():
	try:
		dir = '/var/lib/transmission-daemon/downloads'
		
		com = (f"if [ -d '{dir}' ]; then sudo chmod -R a+rwx '{dir}'; fi")
		ret = subprocess.call(com, shell=True)
		if ret:
			return ret
		else:
			return "Ok."
	except:
		return None



class pbdl():
	def __init__(self):
		self.pbdl_save_dir = "/var/lib/transmission-daemon/downloads"
		self.active_torrents = []
		self.conf = np.readConf()
		self.conf['windows'] = {}
		self.conf['windows']['pbdl'] = {}
		self.poster_img_size_w = 300
		self.poster_img_size_h = 300
		self._id = None
		self.torrents = {}
		self.torrents[self._id] = {}
		self.selected_file = None
		ret = get_permissions()
		self.auto_remove = False
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
		self.category = self.categories['Video']['Main']
		self.results = []
		self.torrent_mgr = False
		self.downloader = False
		self.play_type = 'series'
		self.columns_list = list(np.get_columns('series').keys())
		self.columns_ct = len(self.columns_list)
		self.old_columns_ct = self.columns_ct
		self.query = None
		self.season = None
		self.episode_number = None
		self.series_name = None
		self.title = None
		self.episode_name = None
		try:
			self.pbdl_remote_host = self.conf['pbdl_url']
		except:
			self.pbdl_remote_host = None
			self.conf['pbdl_url'] = None
		if self.pbdl_remote_host == None:
			self.conf['pbdl_url'] = input("Enter ip address of transmission-daemon server: ")
			np.writeConf(self.conf)
			self.pbdl_remote_host = self.conf['pbdl_url']


	def lookup_series_google(self, series_name, season):
		slength = len(str(season))
		if slength >= 1 and '0' not in str(season):
			qseason=('0' + str(season))
		target0 = ("S" + qseason + " E")
		base_url = "https://www.google.com/search?q="
		query=(series_name + "+Season+" + str(season))
		url = (base_url + query)
		r = requests.get(url, allow_redirects=True)
		chunks = r.text.strip().split("\n")
		target1=(' · ')
		target2='href="/imgres?imgurl='
		pos = -1
		lpos = -1
		keepdata = []
		data = None
		for chunk in chunks:
			pos = pos + 1
			if target0 in chunk:
				lines = chunk.split("<div class=")
				for line in lines:
					lpos = lpos + 1
					if target1 in line:
						data = chunks[pos]
						data = data.split("</style>")[1]
						import pickle
						with open("temp.sinfo.pickle", 'wb') as f:
							pickle.dump(chunks[pos], f)
						f.close()
						if data is not None and data not in keepdata:
							keepdata.append(data)
							data = None
		out = {}
		s='<div class="'
		lines = []
		for data in keepdata:
			data = data.split(s)
			lines+=data
		pos = -1
		target2='href="/imgres?imgurl='
		images = []
		ct = 0
		for line in lines:
			item = {}
			pos = pos + 1
			if target2 in line:
				chunks = line.split(target2)
				for chunk in chunks:
					img_url = chunk.split('"')[0]
					if 'http' in img_url:
						s = 'https://'
						pieces = img_url.split(s)
						for p in pieces:
							s = None
							if '.jpg' in p:
								s = '.jpg'
							elif '.png' in p:
								s = '.png'
							elif '.gif' in p:
								s = '.gif'
							if s is not None:
								u = p.split(s)[0]
								u = ('https://' + u + s)
								img_url = urllib.parse.unquote(u)
								images.append(img_url)
								still_path = img_url[0]
			if ' · ' in line:
				#try:
				trimmed = line.split('>')[1].split('<')[0]
				if '% ·' not in trimmed:
					episode_number = int(trimmed.split(' E')[1].split(' ')[0])
					ten = str(episode_number)
					if '0' in ten:
						test = ten[1:2]
						if test != '0':
							episode_number = int(test)
					item['series_name'] = series_name
					item['season'] = int(season)
					item['episode_number'] = int(episode_number)
					item['episode_name'] = trimmed.split(' · ')[1]
					item['overview'] = item['episode_name']
					dpos = pos + 1
					air_date = lines[dpos].split('>')[1].split('<')[0]
					t = datetime.strptime(air_date, '%b %d, %Y')
					ts = (str(t.day) + "-" + str(t.month) + "-" + str(t.year))
					item['air_date'] = ts
					try:
						item['still_path'] = still_path
					except:
						item['still_path'] = None
					out[episode_number] = item
		for episode_number in out:
			item = out[episode_number]
			if item['still_path'] == None:
				try:
					item['still_path'] = images[0]
				except Exception as e:
					np.log(f"Unable to get still shot url: {e}, {images}", 'error')
		out['images'] = images
		out['season'] = season
		out['series_name'] = series_name
		return out



	def display_torrents(self, data=None):
		self.active_torrents = []
		if data == None:
			self.torrents = build_torrents()
		else:
			self.torrents = data
		for _id in list(self.torrents.keys()):
			tid = self.torrents[_id]['tid']
			#try:
			play_type = self.torrents[_id]['play_type']
			name = self.torrents[_id]['name']
			percent = self.torrents[_id]['percent']
			string = (f"{tid}:{_id}:{play_type}:{percent}:{name}")
			self.active_torrents.append(string)
			#except Exception as e:
			#	print ("Exception, 508, {e}")
			#	play_type = self.torrents[_id]['play_type']
			#	#self.torrents[_id]['play_type'] = 'Unknown Type'
			#	percent = self.torrents[_id]['percent']
			#	name = self.torrents[_id]['name']
			#	tid = self.torrents[_id]['tid']
			#	string = (f"{tid}:{_id}:{play_type}:{percent}:{name}")
			#	self.active_torrents.append(string)
		self.pbdl_win['-TORRENT_SELECT-'].update(self.active_torrents)




	def close_pbdl(self, win):
		if win == 'downloader':
			try:
				self.pbdl_dl_win.close()
				self.downloader = False
				return self.downloader
			except Exception as e:
				np.log(f"Unable to close downloader:{e}", 'error')
				return self.downloader
		elif win == 'torrent_mgr':
			try:
				self.pbdl_win.close()
				self.torrent_mgr = False
				return self.torrent_mgr
			except Exception as e:
				np.log(f"Unable to close torrent manager:{e}", 'error')
				return self.torrent_mgr
		else:
			np.log(f"Unknown window:{win}", 'warning')
			return None

	def update_class_data(self):
		for _id in list(self.torrents.keys()):
			play_type = self.torrents[_id]['play_type']
			if play_type is not None:
				columns = list(np.get_columns(play_type).keys())
				uikeys = list(self.values.keys())			
				for column in columns:
					field = (f"-{columns.index(column)}-")
					val = self.values[field]
					print (f"val:{val}, field:{field}, column:{column}, keys:{list(self.torrents[_id].keys())}, values:{list(self.torrents[_id].values())}")
					try:
						if self.torrents[_id][column] != val:
							if val is not None and column != 'tid':
								if column == 'id':
									pass
								if 'ERROR' in val:
									val = 'Unknown'
							self.torrents[_id][column] = val
							np.log(f"Updated Value: Column={column}, Value={val}", 'info')
					except Exception as e:
						np.log(f"Error udpating class: {e}", 'error')
		display_torrents(self.torrents)
	def search_pb(self, query, cat=200):
		results = {}
		if self.conf['debug'] == True:
			np.log("Searching using html function (search_pb)...", 'info')
		query = quote(query)
		base_url = self.get_url()
		url = (base_url + "/search/{query}/1/7/{cat}".format(query=query,cat=cat))
		r = requests.get(url)
		lines = r.content.decode().strip().split("\n")
		magnet = None
		title = None
		pos = -1
		for line in lines:
			t = 'title="Details'
			m = '<a href="magnet:?'
			if title is not None and magnet is not None:
				results[title] = magnet
				magnet = None
				title = None
			if m in line:
				pos = pos + 1
				magnet = line.split('"')[1]
			elif t in line:
				title = line.split('title="')[1].split('"')[0]
				s = 'Details for '
				if s in title:
					title = title.split(s)[1]
		return results


	def get_url(self):
		proxies = {}
		utest = 'class="site"'
		ctest = 'class="country"'
		stest = 'class="status"'
		sptest = 'class="speed"'
		url = "https://piratebayproxy.info"
		r = requests.get(url)
		lines = r.content.decode().split("\n")
		proxies = {}
		pos = -1
		for line in lines:
				line = line.strip()
				if line != '':
						if utest in line:
								data = {}
								pos = pos + 1
								splitter = 'href="'
								url = line.split(splitter)[1].split('"')[0]
								data['url'] = url
						elif ctest in line:
								splitter = 'title="'
								country = line.split(splitter)[1].split('"')[0]
								data['country'] = country
						elif stest in line:
								splitter = '/img/'
								status = line.split(splitter)[1].split('.png')[0]
								data['status'] = status
						elif sptest in line:
								splitter = '">'
								speed = line.split(splitter)[1].split('<')[0]
								data['speed'] = speed
								if status == 'up':
										proxies[speed] = data
				
		speeds = sorted(proxies.keys(), key = lambda x:float(x))
		speed = speeds[0]
		url = proxies[speed]['url']
		return url


	def create_downloader(self):
		search_line = [sg.Input('Enter search query here:', enable_events=True, change_submits=True, key='-PBDL_SEARCH_QUERY-', expand_x=True), sg.Button('Search', key='-PBDL_SEARCH-'), sg.Button('Quit!', key='-DOWNLOADER_EXIT-')]
		results_box = [sg.Listbox(values=self.results, change_submits=True, auto_size_text=True, enable_events=True, expand_x=True, expand_y=True, key='-PBDL_RESULTS-')]
		self.pbdl_search_layout = [
			[search_line],
			[results_box]
		]
		try:
			x = 0
			y = self.conf['windows']['pbdl_dl']['y']
			w = self.conf['windows']['pbdl_dl']['w']
			h = self.conf['windows']['pbdl_dl']['h']
		except:
			self.conf = np.readConf()
			screen = self.conf['screen']
			x, y = self.conf['screens'][screen]['pos_x'], self.conf['screens'][screen]['pos_y']
			try:
				test = self.conf['windows']
			except:
				pass

			w = self.conf['windows']['pbdl_dl']['w']
			h = self.conf['windows']['pbdl_dl']['h']
			np.writeConf(self.conf)
		self.pbdl_dl_win = sg.Window('GUI', self.pbdl_search_layout, no_titlebar=False, location=(x,y), size=(w,h), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
		self.downloader = True
		return self.pbdl_dl_win


	def create_torrent_mgr(self):
		self.play_type = self.conf['play_type']
		self.menu_def = [['&File', ['E&xit']], ['&Toolbar', ['&Remove Torrent', '&Delete Torrent', '&Query TMDB', 'VPN', ['&0 Off', '&1 On', '&2 Status'], 'View &Downloader']], ['&Help', '&About...']]
		self.columns_list = list(np.get_columns(self.play_type).keys())
		self.pbdl_layout = [
		[sg.Listbox(self.active_torrents, expand_x=True, enable_events=True, size=(50,10), key='-TORRENT_SELECT-')],
		[sg.Text('_id:'), sg.Text('', expand_x=True, key='-_id-')],
		[sg.Text('Name:'), sg.Text('', expand_x=True, key='-Name-')],
		[sg.Text('Percent:'), sg.Text('', expand_x=True, key='-Percent-')],
		[sg.Text('Have:'), sg.Text('', expand_x=True, key='-Have-')],
		[sg.Text('ETA:'), sg.Text('', expand_x=True, key='-ETA-')],
		[sg.Text('Upload Rate:'), sg.Text('', expand_x=True, key='-Upload Rate-')],
		[sg.Text('Download Rate:'), sg.Text('', expand_x=True, key='-Download Rate-')],
		[sg.Text('Status:'), sg.Text('', expand_x=True, key='-Status-')],
		[sg.Text('Ratio:'), sg.Text('', expand_x=True, key='-Ratio-')],
		[sg.Listbox([], expand_x=True, expand_y=True, enable_events=True, select_mode='multiple', size=(50,50), key='-TORRENT_FILES-')]

	]
		self.title_bar_layout = [sg.MenubarCustom(self.menu_def, tearoff=False, key='-menubar_key-'), sg.Combo(['series', 'movies', 'music'], self.conf['play_type'] , enable_events=True,key='-MEDIA_TYPE-'), sg.Button("Quit!", key='-Close PBDL-')],
		self.title_bar_frame = sg.Frame(title='', layout = self.title_bar_layout, key='title_bar_frame', expand_x=True, grab=True, element_justification="center", vertical_alignment="top")
		self.media_info_layout = []
		is_active_ckbox = [sg.Button('Refresh From Remote', key='-REFRESH_DATA-'), sg.Button('Load Info', key='-LOAD_INFO-'), sg.Button('Save Info', key='-SAVE_INFO-'), sg.Checkbox(text='Is Active:', auto_size_text=True, change_submits=True, enable_events=True, key='-SET_ACTIVE-'), sg.Checkbox(text='Auto Remove Torrents:', auto_size_text=True, change_submits=True, enable_events=True, key='-AUTO_REMOVE-')]
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

		info_frame = sg.Frame(title='Torrent Data', layout=self.pbdl_layout, key='info_frame', expand_x=True, grab=True, element_justification="left", vertical_alignment="top")
		media_info_frame = sg.Frame(title='Media Info', layout=self.media_info_layout, key='media_info_frame', expand_x=True, grab=True, element_justification="right", vertical_alignment="top")
		self.layout = [[self.title_bar_frame], [info_frame, [media_info_frame, sg.Sizegrip(key='-gui_size-')]]]

		try:
			x = int(self.conf['windows']['pbdl']['x'])
			y = int(self.conf['windows']['pbdl']['y'])
			w = int(self.conf['windows']['pbdl']['w'])
			h = (int(self.conf['windows']['pbdl']['h']) + 100)
		except:
			self.conf = np.readConf()
			screen = self.conf['screen']
			x, y = self.conf['screens'][screen]['pos_x'], self.conf['screens'][screen]['pos_y']
			w = self.conf['windows']['pbdl_dl']['w']
			h = self.conf['windows']['pbdl_dl']['h']
		self.pbdl_win = sg.Window('GUI', self.layout, no_titlebar=False, location=(x,y), size=(600,900), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
		self.torrent_mgr = True
		return self.torrent_mgr


	def remove_torrent(self, _id):
		com = (f"transmission-remote {self.conf['pbdl_url']} -t{_id} -rad")
		ret = send_command(com)
		#build_torrents()
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
			np.log(f"Unable to deal with poster url:{poster_url}", 'error')


	def resize_img(self, img, w=None, h=None):
		if w is None and h is None:
			size = (str(self.poster_img_size_w) + "x" + str(self.poster_img_size_h))
		comstr = ("convert " + str(img) + " -resize " + str(size) + " poster.png")
		ret = send_command(comstr)


	def test_media_type(self, filepath):
		self.filepath = filepath
		self.sinfo = None
		self.season = None
		self.episode_number = None
		try:
			self.sinfo, self.season, self.episode_number = np.seinfo(self.filepath)
			self.play_type = 'series'
			length = len(self.filepath.split(self.sinfo)) - 1
			self.series_name = self.filepath.split(self.sinfo)[0]
			if '/' in self.series_name:
				self.series_name = self.series_name.split('/')[1]
			return 'series', self.series_name, self.sinfo, self.season, self.episode_number
		except Exception as e:
			np.log(f"Filepath doesn't appear to be a series, trying type: movie.", 'info')
			self.play_type = 'movies'
			if '(' in self.filepath and ')' in self.filepath:
				self.year = int(self.filepath.split('(')[1].split(')')[0])
				if self.year >= 1900:
					string = f" ({self.year}) "
					if string in self.filepath:
						title = self.filepath.split(string)[0]

					else:
						string = ('(' + str(self.year) + ')')
						self.title = self.filepath.split(string)[0]
					return 'movies', self.title, self.year
			else:
				self.title = self.filepath.split('.')[0]
				return 'movies', self.title, None


	def enable_vpn(self):
		com = (f"ssh monkey@192.168.2.2 \"nordvpn status\" | grep \"Status\"")
		s = 'Status: '
		self.vpn_status = subprocess.check_output(com, shell=True).decode().strip().split(s)[1]
		if self.conf['debug'] == True:
			np.log("VPN State:{self.vpn_status}", 'info')
		if self.vpn_status == 'Disconnected':
			np.log("WARNING:VPN off...(uncomment the next 3 lines to enable this)", 'warning')
			#com = "ssh monkey@192.168.2.2 \"nordvpn connect\""
			#ret = send_command(com)
		else:
			if self.conf['debug'] == True:
				np.log("VPN alread enabled!", 'info')
		return self.vpn_status



	def select_torrent(self, _id=None):
		if self.torrents[_id]['play_type'] == 'UnknownType':
			self.torrents[_id]['play_type'] = np.get_user_input('Enter Play Type:')
		play_type = self.torrents[_id]['play_type']
		columns = list(np.get_columns(play_type).keys())
		self._id = _id
		print ("Columns:", columns, "Play type:", play_type)
		for column in columns:
			field = (f"-{columns.index(column)}-")
			if column == 'id':
				self.pbdl_win[field].update(_id)
			elif column == 'filepath':
				filepath = self.torrents[_id]['filepath']
			else:
				self.pbdl_win[field].update(self.torrents[_id][column])
			
			#	fname = os.path.basename(filepath)
			#	if fname is not 'Unknown':
			#		if fname == filepath:
			#			fullpath = ssh_get_abspath(fname)[1:]
			#			self.torrents[_id]['filepath'] = (f"/var/transmission-daemon{os.path.sep}downloads{fullpath}")
			#			self.filepath = self.torrents[_id]['filepath']
			#			field = (f"-{self.columns.index('filepath')}-")
				
			#		else:
			#			field = (f"-{self.columns.index('filepath')}-")
			#			self.pbdl_win[field].update("INCOMPLETE DOWNLOAD: File info not yet avaialble.")
			#else:
			#	field = (f"-{self.columns.index(column)}-")
			#	print ("var column field:", field, "column", column)
				#try:
			#	self.pbdl_win[field].update(self.torrents[_id][column])
				#except Exception as e:
				#	np.log(f"Unable to update field {field}, torrent data incomplete: {self.torrents[_id]}. _id={_id}, column={column}, error={e}", 'error')
				#	self.pbdl_win[field].update(f"Unknown {column}")

		self.play_type = self.torrents[_id]['play_type']
		self.pbdl_win['-MEDIA_TYPE-'].update(self.play_type)
		self.update_media_type(self.play_type)
		self.filepath = self.torrents[_id]['filepath']

		self.name = self.torrents[_id]['name']
		self.pbdl_win['-_id-'].update(self._id)
		self.pbdl_win['-Name-'].update(self.name)
		#if self.play_type == 'series':
		#	t_key = ("-" + str(self.columns_list.index('series_name')) + "-")
		#	self.pbdl_win[t_key].update(info['series_name'])
		#	sidx = ("-" + str(self.columns_list.index('season')) + "-")
		#	eidx = ("-" + str(self.columns_list.index('episode_number')) + "-")
		#	if self.episode_number is not None:
		#		self.pbdl_win[eidx].update(info['episode_number'])
		#	self.pbdl_win[sidx].update(info['season'])

		#elif self.play_type == 'movies' or self.play_type == 'music':
		#	fname = info['name']
		#	s = ' ('
		#	if s in fname:
		#		title = fname.split(s)[0]
		#		year = fname.split(s)[1].split(')')[0]
		#	info['title'] = title
		#	info['year'] = year
		#	t_key = ("-" + str(self.columns_list.index('title')) + "-")
		#	y_key = ("-" + str(self.columns_list.index('year')) + "-")			
		#	self.pbdl_win[t_key].update(title)
		#	self.pbdl_win[y_key].update(year)
		#self.pbdl_win['-Percent-'].update(self.torrents[_id]['percent'])
		string = (str(self.torrents[_id]['have']) + " " + str(self.torrents[_id]['size_unit']))
		self.pbdl_win['-Have-'].update(string)
		self.pbdl_win['-ETA-'].update(self.torrents[_id]['eta'])
		self.pbdl_win['-Upload Rate-'].update(self.torrents[_id]['up'])
		self.pbdl_win['-Download Rate-'].update(self.torrents[_id]['down'])
		self.pbdl_win['-Status-'].update(self.torrents[_id]['status'])
		self.pbdl_win['-Ratio-'].update(self.torrents[_id]['ratio'])

		return self.torrents[_id]


	def migrate(self, _id, play_type=None):
		self._id = int(_id)
		ret = False
		if play_type is not None:
			self.play_type = play_type
		if self.selected_file is None:
			self.selected_file = get_files(self._id)
		if self.play_type == 'series':							
			ret = self.add_series(self.torrents[self._id]['info'])
		elif self.play_type == 'movies':
			ret = self.add_movies(self.torrents[self._id]['info'])
		return ret


	def update_media_type(self, play_type=None):
		diff = 0
		extra_length = 0
		self.play_type = play_type
		self.columns_list = list(np.get_columns(self.play_type))
		np.log(f"Type changed:{self.play_type}", 'info')
		if self.columns_ct != 0:
			self.old_columns_ct = self.columns_ct
		else:
			self.columns_ct = len(self.columns_list)
		if self.columns_ct >= self.old_columns_ct:
			ct = self.columns_ct
		elif self.columns_ct <= self.old_columns_ct:
			ct = self.old_columns_ct
		else:
			ct = self.columns_ct
			diff = ct - self.columns_ct
			extra_length = self.columns_ct + diff
		list(np.get_columns(self.play_type).keys())
		self.columns_ct = len(self.columns_list)
		pos = -1
		for column in self.columns_list:
			pos = str(int(pos) + 1)
			d = ("d_" + pos)
			self.pbdl_win[d].update(column)
			if diff >= 0:
				for i in range(self.columns_ct, extra_length):
					d = ("d_" + str(i))
					self.pbdl_win[d].update('None')
		self.pbdl_win.refresh()


	def update_info(self, _id=None, field=None, val=None):
		if field is None:
			field = self.event
		if val is None:
			val = self.values[self.event]
		if _id is not None:
			self._id = int(_id)
		table = self.torrents[_id]['play_type']
		columns = list(np.get_columns(table).keys())
		idx = int(field.split('-')[1])
		column = columns[idx]			
		#try:
		print ("field:", field, "_id", _id)
		pos = int(field.split('-')[1])
		if column == 'isactive':
			idx = self.columns.index('isactive')
			class_stored_field = (f"-{self.columns[idx]}-")
			provided_field = field
			print ("class stored field:", class_stored_field, "provided field:", provided_field, "should be -1-")
			if val != '':
				self.pbdl_win[f"-{self.columns.index('isactive')}-"].update(int(val))
			else:
				self.pbdl_win[f"-{self.columns.index('isactive')}-"].update(val)
			if "'" in val:
				chunks = val.split("'")
				j = "_"
				val = j.join(chunks)
		#except Exception as e:
		#	np.log(f"Update info error:{e}", 'error')
		info = self.torrents[self._id]
		self.torrents[self._id][column] = val
		if self.conf['debug'] == True:
			np.log(f"Update column, column:{column}, value:{self.torrents[self._id][column]}", 'info')
		ret = save_torrent_log(self.torrents)
			

		


	def run(self):
		self.torrents = build_torrents()
		self.display_torrents(self.torrents)
		self.exit = False
		while True:
			if self.exit == True:
				break
			try:
				self.window, self.event, self.values = sg.read_all_windows(timeout=10)
			except Exception as e:
				np.log(f"Exit exception:{e}", 'error')
				self.exit = True
			if self.event=='-Close PBDL-' or self.event == "Exit" or self.event == '-DOWNLOADER_EXIT-':
					save_torrent_log(self.torrents)
					self.exit = True
					self.window.close()
			if self.event == sg.WIN_CLOSED:
				try:
					self.window.close()
					if self.exit == True:
						break
				except:
					break
			else:
				if self.event != '__TIMEOUT__':
					print (self.event)
					if self.event == '-TORRENT_SELECT-':
						val = self.values[self.event][0]
						#self.filepath = val.split(':')[1].split('|')[0]
						_id = int(val.split(':')[0])
						#self.torrents[self._id]['name'] = val.split(':')[1].split('|')[0]
						self.select_torrent(_id)
					elif self.event == '-PBDL_SEARCH_QUERY-':
						self.pbdl_query = self.values[self.event]
					elif self.event == '-Migrate Files-':
						ret = self.migrate(self._id)
						if self.conf['debug'] == True:
							np.log(f"Migration results:{ret}", 'info')
					elif self.event == '-Query TMDB-':
						self.lookup()
					elif self.event == '-AUTO_REMOVE-':
						if self.auto_remove == True:
							self.auto_remove = False
						else:
							self.auto_remove = True
						if self.conf['debug'] == True:
							np.log(f"Auto Remove set to {self.auto_remove}", 'info')
					elif self.event == '-TORRENT_FILES-':
						self.selected_file = self.values[self.event]
					elif self.event == 'Remove':
						if self._id is None:
							np.log(f"Select a torrent file first!", 'warning')
						else:
							self.remove_torrent(self._id)
							np.log(f"Torrent removed:{self._id}", 'info')
							
					elif self.event == '-MEDIA_TYPE-':
						self.play_type = str(self.values[self.event])
						print (f"Play type changed: {self.play_type}")
						self.update_media_type(self.play_type)
					elif self.event == '-PBDL_SEARCH-':
						np.log("searching...", 'info')
						self.results = self.search_pb(self.pbdl_query, self.category)
						self.pbdl_dl_win['-PBDL_RESULTS-'].update(self.results)
					elif self.event == '-PBDL_RESULTS-':
						#try:
						picked = self.values[self.event][0]
						np.log(f"Downloading:{picked}", 'info')
						magnet = self.results[picked]
						#self.enable_vpn()
						com = (f"transmission-remote {self.conf['pbdl_url']} -a \"{magnet}\"")
						r = send_command(com)
						print (r)
						#except Exception as e:
						#	print (e)
						#	np.log("list empty!", 'warning')
					elif self.event == '-0-' or self.event == '-1-' or self.event == '-2-' or self.event == '-3-' or self.event == '-4-' or self.event == '-5-' or self.event == '-6-' or self.event == '-7-' or self.event == '-8-' or self.event == '-9-' or self.event == '-10-':
						val = self.values[self.event]
						ret = self.update_info(self._id, self.event, val)
						np.log("Update info fields result:{ret}", 'info')
					elif self.event == '-SET_ACTIVE-':
						info['isactive'] = int(self.values[self.event])
						self.pbdl_win['-0-'].update(info['isactive'])
					elif self.event == 'View Downloader':
						self.create_downloader()
					elif self.event  == '2 Status':
						np.log(f"event:2 Status:{send_command('nordvpn status')}", 'info')
					elif self.event == '0 Off':
						np.log(f"{send_command('nordvpn disonnect')}", 'info')
					elif self.event == '1 On':
						#self.enable_vpn()
						np.log("VPN Enabled!", 'info')
					elif self.event == '-SAVE_INFO-':
						#self.update_class_data()
						save_torrent_log(self.torrents)
					elif self.event == '-LOAD_INFO-':
						self.torrents = load_saved_data()
						self.display_torrents(self.torrents)
					elif self.event == '-REFRESH_DATA-':
						self.torrents = build_torrents()
						self.display_torrents(self.torrents)
					else:
						np.log("Unknown event: {self.event}, {self.values}", 'warning')
						pass

if __name__ == "__main__":
	pbdl = pbdl()
	pbdl.create_torrent_mgr()
	#pbdl.create_downloader()
	torrents = build_torrents()
	pbdl.run()
