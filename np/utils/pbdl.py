import pickle# be sure to remove this and the pickle dump at the end of build_torrent_data(), line 168
from np.utils.nplayer_db import get_columns
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

tmdb.API_KEY = 'ac1bdc4046a5e71ef8aa0d0bd93f8e9b'
search = tmdb.Search()

def get_permissions():
	try:
		ret = subprocess.check_output('sudo chmod -R a+rwx /var/lib/transmission-daemon/downloads', shell=True)
		return ret
	except:
		return None


class pbdl():
	def __init__(self):
		self.pbdl_save_dir = "/var/lib/transmission-daemon/downloads"
		self.active_torrents = []
		self.conf = np.readConf()
		self.conf['windows'] = {}
		self.conf['windows']['pbdl'] = {}
		self.columns_list = []
		self.columns_ct = 0
		self.old_columns_ct = 0
		self.files = []
		self.media_info = {}
		self.poster_img_size_w = 300
		self.poster_img_size_h = 300
		self.tid = None
		self.selected_file = None
		ret = get_permissions()
		self.auto_remove = False
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
		self.category = self.categories['Video']['Main']
		self.results = []
		self.torrent_mgr = False
		self.downloader = False
		self.play_type = 'series'
		self.query = None
		self.torrents = None


	def build_torrent_data(self):
		self.torrents = self.get_torrents()
		for tid in self.torrents:
			files = self.get_files(tid)
			self.torrents[tid]['info'] = {}
			pos = -1
			for filepath in files:
				if 'sample' not in filepath:
					pos = pos + 1
					self.torrents[tid]['info'][pos] = {}
					type_info = self.test_media_type(filepath)
					self.torrents[tid]['info'][pos]['oldpath'] = ('/var/lib/transmission-daemon/downloads/' + filepath)
					if type_info[0] == 'series':
						play_type, series_name, sinfo, season, episode_number = type_info
						r = search.tv(query=series_name)
						self.torrents[tid]['info'][pos]['air_date'] = r['results'][0]['first_air_date']
						poster = r['results'][0]['poster_path']
						self.torrents[tid]['info'][pos]['poster'] = ('https://image.tmdb.org/t/p/original' + str(poster))
						self.torrents[tid]['info'][pos]['still_path'] = ('https://image.tmdb.org/t/p/original' + str(poster))# additional key for redundancy
						description = r['results'][0]['overview']
						if "'" in description:
							description = description.split("'")
							j = ''
							description = j.join(description)
						self.torrents[tid]['info'][pos]['description'] = description
						self.torrents[tid]['info'][pos]['episode_name'] = 'Unknown'
						
						
						self.torrents[tid]['info'][pos]['isactive'] = 1
						series_name = r['results'][0]['name']
						self.torrents[tid]['tmdbid'] = r['results'][0]['id']
						self.torrents[tid]['info'][pos]['play_type'] = play_type
						self.torrents[tid]['info'][pos]['duration'] = 'null'
						self.torrents[tid]['info'][pos]['md5'] = 'null'
						self.torrents[tid]['info'][pos]['url'] = 'null'
						if self.torrents[tid]['name'] != series_name:
							self.torrents[tid]['name'] = series_name
						self.torrents[tid]['info'][pos]['season'] = season
						self.torrents[tid]['info'][pos]['episode_number'] = episode_number
						self.torrents[tid]['info'][pos]['series_name'] = series_name
						self.torrents[tid]['info'][pos]['tmdbid'] = self.torrents[tid]['tmdbid']
						try:
							tv = tmdb.tv.TV_Episodes(self.torrents[tid]['tmdbid'], season, episode_number)
							info = tv.info()
							self.torrents[tid]['info'][pos]['air_date'] = info['air_date']
							episode_name = info['name']
						except:
							episode_name = 'Unknown'
							pass
						badchars = ['!', '"', "'", ',']
						for char in badchars:
							if char in episode_name:
								episode_name = episode_name.split(char)
								j = ''
								episode_name = j.join(episode_name)
						self.torrents[tid]['info'][pos]['name'] = episode_name
						try:
							self.torrents[tid]['info'][pos]['episode_name'] = episode_name
							description = info['overview']
							if "'" in description:
								description = description.split("'")
								j = ''
								description = j.join(description)
							self.torrents[tid]['info'][pos]['description'] = description
							self.torrents[tid]['info'][pos]['poster'] = info['still_path']
						except Exception as e:
							print ("Unable to get episode info:", e)
						_dir = play_type.capitalize()
						extlen = len(filepath.split('.')) - 1
						ext = str(filepath.split('.')[extlen])
						fname = (series_name + ".S" + str(season) + "E" + str(episode_number) + "." + str(episode_name) + "." + ext)
						newdir = (os.path.sep + 'var' + os.path.sep + "storage" + os.path.sep + _dir + os.path.sep + series_name + os.path.sep + "S" + str(season))
						pathlib.Path(newdir).mkdir(parents=True, exist_ok=True)
						newpath = (newdir + os.path.sep + fname)
						print (newpath)
						self.torrents[tid]['info'][pos]['filepath'] = newpath
		with open ("/home/monkey/temp.pickle", 'wb') as f:
			pickle.dump(self.torrents, f)
		f.close()
		return self.torrents


	def move_finished(self):
		if self.torrents == None:
			self.torrents = self.build_torrent_data()
		for tid in torrents:
			data = torrents[tid]
			



	def close_pbdl(self, win):
		if win == 'downloader':
			try:
				self.pbdl_dl_win.close()
				self.downloader = False
				return self.downloader
			except Exception as e:
				print ("Unable to close downloader:", e)
				return self.downloader
		elif win == 'torrent_mgr':
			try:
				self.pbdl_win.close()
				self.torrent_mgr = False
				return self.torrent_mgr
			except Exception as e:
				print ("Unable to close torrent manager:", e)
				return self.torrent_mgr
		else:
			print ("Unknown window:", win)
			return None


	def get_results_html(self, query, cat=200):
		results = {}
		print ("search html")
		query = quote(query)
		base_url = self.get_url()
		url = (base_url + "/search/{query}/1/7/{cat}".format(query=query,cat=cat))
		r = requests.get(url)
		lines = r.content.decode().strip().split("\n")
		magnet = None
		title = None
		pos = -1
		for line in lines:
				t = 'class="detLink" title="'
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
						
	def get_results_api(self, query, cat=200):
		query = quote(query)
		base_url = self.get_url()
		s = 'https'		
		if s in base_url:
				base_url = base_url.split(s)[1]
				base_url = ("http" + base_url)
		url = (base_url + "/api?url=/q.php?q={query}&cat={cat}&sort=7".format(query=query,cat=cat))
		r = requests.get(url)
		out = r.content.decode().strip()
		test_string = '<title>Not Found | The Pirate Bay'
		if test_string in out:
				return False
		json_data = json.loads(out)
		results = {}
		for data in json_data:
				keys = list(data.keys())
				vals = list(data.values())
				pos = -1
				for key in keys:
						pos = pos + 1
						val = vals[pos]
						if key == 'name':
								name = val
						elif key == 'info_hash':
								info_hash = val
						elif key == 'seeders':
								seeders = int(val)
								if seeders >= 0:
										dkey = (name + " (Seeds: " + str(seeders) + ")")								
										results[dkey] = {}
										results[dkey]['info_hash'] = info_hash
										results[dkey]['seeders'] = seeders
		return results
								
#magnet = "magnet:?xt=urn:btih:{info_hash}&dn={name}&tr=udp://tracker.coppersurfer.tk:6969/announce&tr=udp://tracker.openbittorrent.com:6969/announce&tr=udp://tracker.opentrackr.org:1337&tr=udp://tracker.leechers-paradise.org:6969/announce&tr=udp://tracker.dler.org:6969/announce&tr=udp://opentracker.i2p.rocks:6969/announce&tr=udp://47.ip-51-68-199.eu:6969/announce&tr=udp://tracker.internetwarriors.net:1337/announce&tr=udp://9.rarbg.to:2920/announce&tr=udp://tracker.pirateparty.gr:6969/announce&tr=udp://tracker.cyberia.is:6969/announce"

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


	def get_magnet(self, query, cat=None):
		if cat == None:
			cat = self.category
		self.results = self.get_results_api(query, cat)
		if self.results:
			return self.results
		else:
			self.results = self.get_results_html(query, cat)
			return self.results


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
		try:
			self.pbdl_win['-TORRENT_SELECT-'].update(self.active_torrents)
		except:
			pass
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
		try:
			self.pbdl_win['-TORRENT_FILES-'].update(self.files)
		except:
			pass
		return self.files

		
	def create_downloader(self):
		search_line = [sg.Input('Enter search query here:', enable_events=True, change_submits=True, key='-PBDL_SEARCH_QUERY-', expand_x=True), sg.Button('Search', key='-PBDL_SEARCH-'), sg.Button('Quit Downloader', '-DOWNLOADER_EXIT-')]
		results_box = [sg.Listbox(values=self.results, change_submits=True, auto_size_text=True, enable_events=True, expand_x=True, expand_y=True, key='-PBDL_RESULTS-')]
		self.pbdl_search_layout = [
			[search_line],
			[results_box]
		]
		try:
			x = self.conf['windows']['pbdl_dl']['x']
			y = self.conf['windows']['pbdl_dl']['y']
			w = self.conf['windows']['pbdl_dl']['w']
			h = self.conf['windows']['pbdl_dl']['h']
		except:
			self.conf = np.readConf()
			self.conf['windows'] = np.init_window_position()
			np.writeConf(self.conf)
			x = self.conf['windows']['pbdl_dl']['x']
			y = self.conf['windows']['pbdl_dl']['y']
			w = self.conf['windows']['pbdl_dl']['w']
			h = self.conf['windows']['pbdl_dl']['h']
		self.pbdl_dl_win = sg.Window('GUI', self.pbdl_search_layout, no_titlebar=False, location=(x,y), size=(w,h), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
		self.downloader = True
		return self.pbdl_dl_win


	def create_window(self):
		self.play_type = self.conf['play_type']
		self.menu_def = [['&File', ['E&xit']], ['&Toolbar', ['&Remove Torrent', '&Delete Torrent', '&Query TMDB', 'VPN', ['&0 Off', '&1 On', '&2 Status']]], ['&Help', '&About...']]
		if self.play_type == 'movies':
			self.columns_list = ['isactive', 'title', 'tmdbid', 'year', 'release_date', 'duration', 'description', 'poster', 'filepath', 'md5', 'url']
		elif self.play_type == 'series' or self.play_type == 'videos':
			self.columns_list = ['isactive', 'series_name', 'tmdbid', 'season', 'episode_number', 'episode_name', 'description', 'air_date', 'still_path', 'duration', 'filepath', 'md5', 'url']
		elif self.play_type == 'music':
			self.columns_list = ['isactive', 'title', 'accoustic_id', 'album', 'album_id', 'artist_id', 'year', 'artist', 'track', 'track_ct', 'filepath']
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
		[sg.Listbox(self.files, expand_x=True, expand_y=True, enable_events=True, select_mode='multiple', size=(50,50), key='-TORRENT_FILES-')]

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
			h = (int(self.conf['windows']['pbdl']['h']) + 100)
		except:
			self.conf['windows'] = np.init_window_position()
			x = int(self.conf['windows']['pbdl']['x'])
			y = int(self.conf['windows']['pbdl']['y'])
			w = int(self.conf['windows']['pbdl']['w'])
			h = (int(self.conf['windows']['pbdl']['h']) +100)
		self.pbdl_win = sg.Window('GUI', self.layout, no_titlebar=True, location=(x,y), size=(w,h), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
		self.torrent_mgr = True
		return self.torrent_mgr


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


	def test_media_type(self, filepath):
		sinfo = None
		season = None
		episode_number = None
		sinfo, season, episode_number = np.seinfo(filepath)
		testsinfo = ('.' + sinfo)
		if testsinfo in filepath:
			sinfo = testsinfo
		if sinfo is not None and season is not None and episode_number is not None:
			length = len(filepath.split(sinfo)) - 1
			series_name = filepath.split(sinfo)[0]
			if '/' in series_name:
				series_name = series_name.split('/')[1]
			return 'series', series_name, sinfo, season, episode_number
			#except Exception as e:
			#	print ("can't split filepath:", e, filepath, sinfo)
			#	return None
		if '(' in filepath and ')' in filepath:
			year = int(filepath.split('(')[1].split(')')[0])
			if year >= 1900:
				string = (' (' + str(year) + ')')
				if string in filepath:
					title = filepath.split(string)[0].split('/')[1]
				else:
					string = ('(' + str(year) + ')')
					title = filepath.split(string)[0].split('/')[1]
				return 'movie', title, year
		


	def lookup(self, _files=None):
		if self.play_type == None:
			conf = np.readConf()
			self.play_type = conf['play_type']
		if self.play_type == 'movies':
			self.columns_list = ['isactive', 'title', 'tmdbid', 'year', 'release_date', 'duration', 'description', 'poster', 'filepath', 'md5', 'url']
		elif self.play_type == 'series' or self.play_type == 'videos':
			self.columns_list = ['isactive', 'series_name', 'tmdbid', 'season', 'episode_number', 'episode_name', 'description', 'air_date', 'still_path', 'duration', 'filepath', 'md5', 'url']
		elif self.play_type == 'music':
			self.columns_list = ['isactive', 'title', 'accoustic_id', 'album', 'album_id', 'artist_id', 'year', 'artist', 'track', 'track_ct', 'filepath']
						
		if _files is None:
			if self.selected_file is None:
				self.selected_file = self.get_files(self.tid)
		else:
			self.selected_file = _files
		self.add_to_db_data = []
		if type(self.selected_file) != list:
			self.selected_file = [self.selected_file]
		for item in self.selected_file:
			if item is not None:
				self.sourcePath = ('/var/lib/transmission-daemon/downloads' + os.path.sep + item)
				if self.play_type == 'series':
					try:
						self.sinfo, self.season, self.episode_number = np.seinfo(item)
					except:
						self.sinfo = item.split('.')[1]
						self.season = self.sinfo.split('E')[0].split('S')[1]
						self.episode_number = self.sinfo.split('E')[1]
					sidx = ("-" + str(self.columns_list.index('season')) + "-")
					eidx = ("-" + str(self.columns_list.index('episode_number')) + "-")
					nidx = ("-" + str(self.columns_list.index('series_name')) + "-")
					self.series_name = self.values[nidx]
					if "'" in self.series_name:
						chunks = self.series_name.split("'")
						j = "_"
						self.series_name = j.join(chunks)
					self.pbdl_win[sidx].update(self.season)
					self.pbdl_win[eidx].update(self.episode_number)
					print ("name, season, e-number:", self.series_name, self.season, self.episode_number)
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
					info = np.query_series(self.series_name, self.season, self.episode_number)
					if info['response'][0] == 'Error:':
						info = lookup_series_google(self.series_name, self.season)
						info = info[self.episode_number]
					self.media_info = info
					self.add_to_db_data.append(self.media_info)
					#print (type(self.media_info), self.media_info)
					self.still_path = str(self.media_info['still_path'])
					if 'http://' not in self.still_path and 'https://' not in self.still_path:
						poster = ("https://image.tmdb.org/t/p/original" + self.still_path)
					else:
						poster = self.still_path
					self.get_poster(poster)
					#print ("Series lookup results:", self.media_info)
				
				elif self.play_type == 'movies':
					try:
						title = self.media_info['title']
						try:
							year = self.media_info['year']
							query = (str(title) + " (" + str(year) + ")")
						except:
							query = title
						print ("Searching:", query)
						self.media_info = np.lookup_movies(query)
						if self.selected_file is not None:
							ext = self.selected_file[0].split('.')
							l = len(ext) - 1
							ext = ext[l]
							self.media_info['filepath'] = ("/var/storage/Movies/" + str(title) + " (" + str(year) + ")/" + str(title) + " (" + str(year) + ")." + str(ext))
						keys = list(self.media_info.keys())
						if self.media_info is not None:
							self.media_info['md5'] = 'null'
							if self.media_info['url'] is None:
								self.media_info['url'] = 'null'
							for key in keys:
								val = self.media_info[key]
								field = ("-" + str(self.columns_list.index(key)) + "-")
								self.pbdl_win[field].update(val)
								if key == 'isactive':
									self.pbdl_win['-SET_ACTIVE-'].update(int(val))
						self.get_poster(self.media_info['poster'])
						self.add_to_db_data.append(self.media_info)
					except Exception as e:
						print ("Unable to lookup data:", e)
								
			
	def add_series(self, add_to_db_data=None):
		self.isactive = 1
		if series_data == None:
			add_to_db_data = self.add_to_db_data
		for series_data in add_to_db_data:
			try:
				self.series_name = series_data['series_name']
				self.tmdbid = series_data['tmdbid']
				self.season = series_data['season']
				self.episode_number = series_data['episode_number']
				self.episode_name = series_data['episode_name']
				self.description = series_data['description']
				self.air_date = series_data['air_date']
				self.still_path = series_data['still_path']
				self.duration = series_data['duration']
				self.filepath = series_data['filepath']
				self.md5 = series_data['md5']
				self.url = series_data['url']
			except Exception as e:
				print ("clusterfuck:", e)
				return False
			try:
				self.sourcePath = urllib.parse.unquote(series_data['source_path'])
			except:
				self.sourcePath = input("Enter source path: ")
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


	def add_movies(self, add_to_db_data=None):
		self.isactive = 1
		if add_to_db_data == None:
			add_to_db_data = self.add_to_db_data
		for movie_data in add_to_db_data:
			keys = list(movie_data.keys())
			pos = -1
			for key in keys:
				val = movie_data[key]
				print ("val:", val)
				if val is not None and key != 'title' and key != 'filepath':
					if ' ' in str(val) or "'" in str(val) or '"' in str(val):
						val = urllib.parse.quote(val)
						movie_data[key] = val
			sdir = "/var/lib/transmission-daemon/downloads/"
			if sdir not in self.sourcePath:
				self.sourcePath = ("/var/lib/transmission-daemon/downloads/" + str(self.selected_file[0]))
			self.destinationPath = urllib.parse.unquote(movie_data['filepath'])
			p = pathlib.Path(self.destinationPath)
			new_dir = (p.parent.absolute())
			pathlib.Path(new_dir).mkdir(parents=True, exist_ok=True)
			#np.write_log(("pbdl.py, add_movies: media info:", self.media_info), "INFO")
			vars = "isactive, tmdbid, title, year, release_date, duration, description, poster, filepath, md5, url"
			values = ("1, '" + str(self.media_info['tmdbid']) + "', '" + str(self.media_info['title']) + "', '" + str(self.media_info['year']) + "', '" + str(self.media_info['release_date']) + "', '" + str(self.media_info['duration']) + "', '" + str(self.media_info['description']) + "', '" + str(self.media_info['poster']) + "', '" + str(self.destinationPath) + "', 'None', 'None'")
			self.insert_query_string = ("INSERT INTO movies (" + vars + ") VALUES(" + values + ");")
			ret = self.add_to_db(self.insert_query_string)
			if ret:
				print ("Success!")
			else:
				print ("Unknown exception...ret=", ret)



	def add_to_db(self, play_type='series', insert_query_string=None):
		if insert_query_string is None:
			try:
				insert_query_string = self.insert_query_string
			except Exception as e:
				print ("query string not set!", e)
				return False
		ret = np.addtodb(self.play_type, insert_query_string)
		print ("ret:", ret)
		if ret == True:
			try:
				shutil.move(self.sourcePath, self.destinationPath)
				if self.auto_remove == True:
					ret = self.remove_torrent(self.tid)
					print ("Torrent removal:", ret)
				return True
			except Exception as e:
				self.auto_remove = False
				print ("line 294, pbdl.py, file migration failed!", e, self.sourcePath, self.destinationPath)
				return False
		else:
			print ("Add to db failed!", ret)



	def run(self):
		while True:
			self.window, self.event, self.values = sg.read_all_windows(timeout=10)
			if self.event == sg.WIN_CLOSED or self.event=='-Close PBDL-' or self.event == "Exit" or self.event == '-DOWNLOADER_EXIT-':
				self.window.close()
				break
			else:
				if self.event != '__TIMEOUT__':
					if self.event == '-TORRENT_SELECT-':
						self.tid = self.values[self.event][0]
						self.tid = self.tid.split(':')[0]
						self.pbdl_win['-TID-'].update(self.tid)
						self.pbdl_win['-Name-'].update(self.torrent_data[self.tid]['name'])
						if self.play_type == 'series':
							self.media_info['series_name'] = self.torrent_data[self.tid]['name']
							self.pbdl_win['-1-'].update(self.media_info['series_name'])
						elif self.play_type == 'movies' or self.play_type == 'music':
							name = str(self.torrent_data[self.tid]['name'])
							if '(' in name and ')' in name:
								title = name.split('(')[0].strip()
								year = name.split('(')[1].split(')')[0]
								self.media_info['title'] = title
								self.media_info['year'] = year
								t_key = ("-" + str(self.columns_list.index('title')) + "-")
								y_key = ("-" + str(self.columns_list.index('year')) + "-")
								
								self.pbdl_win[t_key].update(self.media_info['title'])
								self.pbdl_win[y_key].update(self.media_info['year'])
							else:
								self.pbdl_win[self.columns_list.index('title')].update(name)
						self.pbdl_win['-Percent-'].update(self.torrent_data[self.tid]['percent'])
						string = (str(self.torrent_data[self.tid]['have']) + " " + str(self.torrent_data[self.tid]['size_unit']))
						self.pbdl_win['-Have-'].update(string)
						self.pbdl_win['-ETA-'].update(self.torrent_data[self.tid]['eta'])
						self.pbdl_win['-Upload Rate-'].update(self.torrent_data[self.tid]['up'])
						self.pbdl_win['-Download Rate-'].update(self.torrent_data[self.tid]['down'])
						self.pbdl_win['-Status-'].update(self.torrent_data[self.tid]['status'])
						self.pbdl_win['-Ratio-'].update(self.torrent_data[self.tid]['ratio'])
						self.torrent_data[self.tid]['files'] = self.get_files(self.tid)
					elif self.event == '-PBDL_SEARCH_QUERY-':
						self.pbdl_query = self.values[self.event]
						print (self.pbdl_query)
					elif self.event == '-Migrate Files-':
						if self.selected_file is None:
							self.selected_file = self.get_files(self.tid)
						if self.play_type == 'series':							
							self.add_series(self.media_info)
						elif self.play_type == 'movies':
							self.add_movies(self.media_info)
					elif self.event == '-Query TMDB-':
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
						print ("ct, old_ct, ct, diff:", self.columns_ct, self.old_columns_ct, ct, diff)
						extra_length = self.columns_ct + diff
						if self.play_type == 'movies':
							self.columns_list = ['isactive', 'title', 'tmdbid', 'year', 'release_date', 'duration', 'description', 'poster', 'filepath', 'md5', 'url']
						elif self.play_type == 'series' or self.play_type == 'videos':
							self.columns_list = ['isactive', 'series_name', 'tmdbid', 'season', 'episode_number', 'episode_name', 'description', 'air_date', 'still_path', 'duration', 'filepath', 'md5', 'url']
						elif self.play_type == 'music':
							self.columns_list = ['isactive', 'title', 'accoustic_id', 'album', 'album_id', 'artist_id', 'year', 'artist', 'track', 'track_ct', 'filepath']
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
					elif self.event == '-PBDL_SEARCH-':
						print ("searching...")
						self.results = self.get_magnet(self.pbdl_query, self.category)
						self.pbdl_dl_win['-PBDL_RESULTS-'].update(self.results)
					elif self.event == '-PBDL_RESULTS-':
						print (self.event, self.values[self.event])
						picked = self.values[self.event][0]
						
						print ("Downloading:", picked)
						magnet = self.results[picked]
						com = 'ret=$(ping -c 1 -W 1 192.168.2.1 | grep "100% packet loss"); if [ -n "$ret" ]; then echo 1; else echo 0; fi'
						vpn_status = self.send_command(com)
						print ("VPN State:", vpn_status)
						if vpn_status == 0:
							print ("VPN off. Enabling...")
							com = "nordvpn connect"
							ret = self.send_command(com)
							print (ret)
						else:
							print ("VPN alread enabled!")
						com = ("transmission-remote -a '" + str(magnet) + "'")
						r = self.send_command(com)
						print (r)

						
					elif self.event == '-0-' or self.event == '-1-' or self.event == '-2-' or self.event == '-3-' or self.event == '-4-' or self.event == '-5-' or self.event == '-6-' or self.event == '-7-' or self.event == '-8-' or self.event == '-9-' or self.event == '-10-':
						try:
							val = self.values[self.event]
							pos = int(self.event.split('-')[1])
							column = self.columns_list[pos]
							if column == 'isactive':
								self.pbdl_win['-SET_ACTIVE-'].update(int(val))
							if "'" in val:
								chunks = val.split("'")
								j = "_"
								val = j.join(chunks)
							self.media_info[column] = val
							self.id = self.values[self.event][0]
							print (self.media_info)
						except:
							pass
					elif self.event == '-SET_ACTIVE-':
						print (self.values)
						self.media_info['isactive'] = int(self.values[self.event])
						self.pbdl_win['-0-'].update(self.media_info['isactive'])
					else:
						#pass
						print (self.event, self.values)

if __name__ == "__main__":
	pbdl = pbdl()
	pbdl.create_window()
	#pbdl.get_torrents()
	pbdl.build_torrent_data()
	pbdl.run()
