import pickle# be sure to remove this and the pickle dump at the end of build_torrent_data(), line 168
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
		self.poster_img_size_w = 300
		self.poster_img_size_h = 300
		self.tid = None
		self.torrents = {}
		self.torrents[self.tid] = {}
		self.torrents[self.tid]['info'] = {}
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
		self.query = None
		self.season = None
		self.episode_number = None
		self.series_name = None
		self.title = None
		self.episode_name = None


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
					print ("Unable to get still shot url:", e, images)
		out['images'] = images
		out['season'] = season
		out['series_name'] = series_name
		print (out['images'])
		return out



	def get_torrents(self):
		torrents = {}
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
		for line in outlist:
			data = {}
			if line is not None:
				if line.split('|')[0] == 'ID' or line.split('|')[0] == 'Sum:':
					pass
				else:

					chunks = line.split('|')
					tid = int(chunks[0])
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
					if string not in self.active_torrents:
						self.active_torrents.append(string)
					torrents[tid] = data
		try:
			self.pbdl_win['-TORRENT_SELECT-'].update(self.active_torrents)
			
		except:
			pass
		self.torrents = torrents
		return torrents



	def build_torrent_data(self):
		print ("Building torrent data. Please wait a moment...")
		torrents = self.get_torrents()
		for tid in torrents:
			tid = int(tid)
			files = self.get_files(tid)
			torrents[tid]['info'] = {}
			info = torrents[tid]['info']
			for filepath in files:
				if 'sample' not in filepath:
					info[filepath] = {}
					type_info = self.test_media_type(filepath)
					if type_info[0] == 'series':
						play_type, series_name, sinfo, season, episode_number = type_info
					else:
						play_type, title, year = type_info
					print ("Play type:", play_type)
					info[filepath]['oldpath'] = ('/var/lib/transmission-daemon/downloads/' + filepath)
					if play_type == 'series':
						info[filepath]['play_type'] = play_type
						r = search.tv(query=series_name)
						info[filepath]['air_date'] = r['results'][0]['first_air_date']
						poster = r['results'][0]['poster_path']
						info[filepath]['poster'] = ('https://image.tmdb.org/t/p/original' + str(poster))
						info[filepath]['still_path'] = ('https://image.tmdb.org/t/p/original' + str(poster))# additional key for redundancy
						description = r['results'][0]['overview']
						if "'" in description:
							description = description.split("'")
							j = ''
							description = j.join(description)
						info[filepath]['description'] = description
						info[filepath]['episode_name'] = 'Unknown'
						
						
						info[filepath]['isactive'] = 1
						series_name = r['results'][0]['name']
						info['tmdbid'] = r['results'][0]['id']
						info[filepath]['play_type'] = play_type
						info[filepath]['duration'] = 'null'
						info[filepath]['md5'] = 'null'
						info[filepath]['url'] = 'null'
						if torrents[tid]['name'] != series_name:
							torrents[tid]['name'] = series_name
						info[filepath]['season'] = season
						info[filepath]['episode_number'] = episode_number
						info[filepath]['series_name'] = series_name
						try:
							info['tmdbid'] = torrents[tid]['tmdbid']
						except:
							info['tmdbid'] = 'null'
						try:
							tv = tmdb.tv.TV_Episodes(torrents[tid]['tmdbid'], season, episode_number)
							d = tv.info()
							info[filepath]['air_date'] = d['air_date']
							episode_name = info['name']
						except Exception as e:
							print ("Series name, season:", series_name, season)
							d = self.lookup_series_google(series_name, season)
							kt = list(d.keys())[0]
							if type(kt) == str:
								episode_name = d[episode_number]['episode_name']
							else:
								episode_name = d[int(episode_number)]['episode_name']
							pass
						badchars = ['!', '"', "'", ',']
						for char in badchars:
							if char in episode_name:
								episode_name = episode_name.split(char)
								j = ''
								episode_name = j.join(episode_name)
						info[filepath]['name'] = episode_name
						try:
							info[filepath]['episode_name'] = episode_name
							description = info['overview']
							if "'" in description:
								description = description.split("'")
								j = ''
								description = j.join(description)
							info[filepath]['description'] = description
							info[filepath]['poster'] = info[filepath]['still_path']
						except Exception as e:
							print ("Unable to get episode info:", e)
						_dir = play_type.capitalize()
						extlen = len(filepath.split('.')) - 1
						ext = str(filepath.split('.')[extlen])
						fname = (series_name + ".S" + str(season) + "E" + str(episode_number) + "." + str(episode_name) + "." + ext)
						newdir = (os.path.sep + 'var' + os.path.sep + "storage" + os.path.sep + _dir + os.path.sep + series_name + os.path.sep + "S" + str(season))
						pathlib.Path(newdir).mkdir(parents=True, exist_ok=True)
						newpath = (newdir + os.path.sep + fname)
						#print (newpath)
						info[filepath]['filepath'] = newpath
					else:
						print ("Movie info:", info[filepath])
		with open ("/home/monkey/temp.pickle", 'wb') as f:
			pickle.dump(torrents, f)
		f.close()
		print ("Torrents loaded!")
		self.torrents = torrents
		return torrents


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


	def search_pb(self, query, cat=200):
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


	def send_command(self, com):
		try:
			ret = subprocess.check_output(com, stderr=subprocess.STDOUT, shell=True).decode().split("\n")
			if ret is not None:
				return ret
			else:
				return True
		except Exception as e:
			print ("Command failed:", e, com)
			return False


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


	def get_files(self, tid):
		string = ("transmission-remote -t" + str(tid) + " --files")
		data = self.send_command(string)
		pos = -1
		files = []
		for line in data:
			pos = pos + 1
			if pos >= 0:
				if 'GB ' in line:
					_file = line.split('GB ')[1].strip()
					files.append(_file)
				elif 'MB ' in line:
					_file = line.split('MB ')[1].strip()
					files.append(_file)
				elif 'KB ' in line:
					_file = line.split('KB ')[1].strip()
					files.append(_file)
				else:
					pass
		try:
			self.pbdl_win['-TORRENT_FILES-'].update(files)
		except:
			pass
		return files


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
			self.conf['windows'] = np.init_window_position()
			np.writeConf(self.conf)
			x = 0
			y = self.conf['windows']['pbdl_dl']['y']
			w = self.conf['windows']['pbdl_dl']['w']
			h = self.conf['windows']['pbdl_dl']['h']
		self.pbdl_dl_win = sg.Window('GUI', self.pbdl_search_layout, no_titlebar=False, location=(x,y), size=(w,h), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
		self.downloader = True
		return self.pbdl_dl_win


	def create_window(self):
		self.play_type = self.conf['play_type']
		self.menu_def = [['&File', ['E&xit']], ['&Toolbar', ['&Remove Torrent', '&Delete Torrent', '&Query TMDB', 'VPN', ['&0 Off', '&1 On', '&2 Status'], 'View &Downloader']], ['&Help', '&About...']]
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
		[sg.Listbox([], expand_x=True, expand_y=True, enable_events=True, select_mode='multiple', size=(50,50), key='-TORRENT_FILES-')]

	]
		self.title_bar_layout = [sg.MenubarCustom(self.menu_def, tearoff=False, key='-menubar_key-'), sg.Combo(['series', 'movies', 'music'], self.conf['play_type'] , enable_events=True,key='-MEDIA_TYPE-'), sg.Button("Quit!", key='-Close PBDL-')],
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
			print ("Unable to extract season info from file path: (not series???)", self.filepath)
			self.play_type = 'movies'
			if '(' in self.filepath and ')' in self.filepath:
				self.year = int(self.filepath.split('(')[1].split(')')[0])
				if self.year >= 1900:
					string = (' (' + str(self.year) + ')')
					if string in self.filepath:
						title = self.filepath.split(string)[0].split('/')[1]
					else:
						string = ('(' + str(self.year) + ')')
						self.title = self.filepath.split(string)[0].split('/')[1]
					return 'movie', self.title, self.year
			else:
				self.title = self.filepath.split('.')[0]
				return 'movie', self.title, None


	def enable_vpn(self):
		com = 'nordvpn status | cut =d " " -f 2'
		self.vpn_status = self.send_command(com)
		print ("VPN State:", vpn_status)
		if self.vpn_status == 'Disconnected':
			print ("VPN off. Enabling...")
			com = "nordvpn connect"
			ret = self.send_command(com)
			print (ret)
		else:
			print ("VPN alread enabled!", self.vpn_status)


	def select_torrent(self, filepath=None, play_type = None):
		if play_type is not None:
			self.play_type = play_type
		if filepath is not None:
			self.filepath = filepath
		info = self.torrents[self.tid]['info']
		name = self.torrents[self.tid]['name']
		self.pbdl_win['-TID-'].update(self.tid)
		self.pbdl_win['-Name-'].update(name)
		self.play_type = info[self.filepath]['play_type']
		if self.play_type == 'series':
			t_key = ("-" + str(self.columns_list.index('series_name')) + "-")
			self.pbdl_win[t_key].update(info[filepath]['series_name'])
			sidx = ("-" + str(self.columns_list.index('season')) + "-")
			eidx = ("-" + str(self.columns_list.index('episode_number')) + "-")
			if self.episode_number is not None:
				self.pbdl_win[eidx].update(info[filepath]['episode_number'])
			self.pbdl_win[sidx].update(info[filepath]['season'])

		elif self.play_type == 'movies' or self.play_type == 'music':
			title = info[filepath]['title']
			year = info[filepath]['year']
			t_key = ("-" + str(self.columns_list.index('title')) + "-")
			y_key = ("-" + str(self.columns_list.index('year')) + "-")			
			self.pbdl_win[t_key].update(title)
			self.pbdl_win[y_key].update(year)
			self.pbdl_win[self.columns_list.index('title')].update(name)
		self.pbdl_win['-Percent-'].update(self.torrents[self.tid]['percent'])
		string = (str(self.torrents[self.tid]['have']) + " " + str(self.torrents[self.tid]['size_unit']))
		self.pbdl_win['-Have-'].update(string)
		self.pbdl_win['-ETA-'].update(self.torrents[self.tid]['eta'])
		self.pbdl_win['-Upload Rate-'].update(self.torrents[self.tid]['up'])
		self.pbdl_win['-Download Rate-'].update(self.torrents[self.tid]['down'])
		self.pbdl_win['-Status-'].update(self.torrents[self.tid]['status'])
		self.pbdl_win['-Ratio-'].update(self.torrents[self.tid]['ratio'])
		self.torrents[self.tid]['files'] = self.get_files(self.tid)

		return self.torrents[self.tid]


	def migrate(self, tid, play_type=None):
		self.tid = int(tid)
		ret = False
		if play_type is not None:
			self.play_type = play_type
		if self.selected_file is None:
			self.selected_file = self.get_files(self.tid)
		if self.play_type == 'series':							
			ret = self.add_series(self.torrents[self.tid]['info'])
		elif self.play_type == 'movies':
			ret = self.add_movies(self.torrents[self.tid]['info'])
		return ret


	def update_media_type(self, play_type=None):
		if play_type is not None:
			self.play_type = play_type
		else:
			self.play_type = str(self.values[self.event])
		print ("Type changed:", self.play_type)
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
			#print ("ct, old_ct, ct, diff:", self.columns_ct, self.old_columns_ct, ct, diff)
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


	def update_info(self, tid=None, key=None):
		if key is None:
			key = self.values[self.event]
		if tid is not None:
			self.tid = int(tid)
		try:
			pos = int(key.split('-')[1])
			column = self.columns_list[pos]
			if column == 'isactive':
				self.pbdl_win['-SET_ACTIVE-'].update(int(key))
				if "'" in key:
					chunks = key.split("'")
					j = "_"
					key = j.join(chunks)
		except Exception as e:
			print ("Update info error:", e)
		info = self.torrents[self.tid]['info']
		for column in info:
			val = info[column]
			print ("Update column, val:", column, val)
			if column == 'series_name':
				self.series_name = val
			elif column == 'season':
				self.season = int(val)
			elif column == 'episode_number':
				self.episode_number = int(val)
			elif column == 'isactive':
				self.isactive = val

			


	def run(self):
		self.exit = False
		while True:
			if self.exit == True:
				break
			try:
				self.window, self.event, self.values = sg.read_all_windows(timeout=10)
			except Exception as e:
				print ("Exit exception:", e)
				self.exit = True
			if self.event=='-Close PBDL-' or self.event == "Exit" or self.event == '-DOWNLOADER_EXIT-':
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
						self.filepath = int(self.values[self.event][0].split(':')[1])
						self.select_torrent(self.filepath)
						self.event = None
					elif self.event == '-PBDL_SEARCH_QUERY-':
						self.pbdl_query = self.values[self.event]
					elif self.event == '-Migrate Files-':
						ret = self.migrate(self.tid)
						print ("Migration results:", ret)
					elif self.event == '-Query TMDB-':
						self.lookup()
					elif self.event == '-AUTO_REMOVE-':
						if self.auto_remove == True:
							self.auto_remove = False
						else:
							self.auto_remove = True
						print ("Auto Remove set to ", self.auto_remove)
					elif self.event == '-TORRENT_FILES-':
						self.selected_file = self.values[self.event]
					elif self.event == 'Remove':
						if self.tid is None:
							print ("Select a torrent file first!")
						else:
							self.remove_torrent(self.tid)
							print ("Torrent removed:", self.tid)
							
					elif self.event == '-MEDIA_TYPE-':
						self.play_type = str(self.values[self.event])
						self.update_media_type(self.play_type)
					elif self.event == '-PBDL_SEARCH-':
						print ("searching...")
						self.results = self.search_pb(self.pbdl_query, self.category)
						self.pbdl_dl_win['-PBDL_RESULTS-'].update(self.results)
					elif self.event == '-PBDL_RESULTS-':
						#print (self.event)
						picked = self.values[self.event][0]
						print ("Downloading:", picked)
						magnet = self.results[picked]
						self.enable_vpn()
						com = ("transmission-remote -a '" + str(magnet) + "'")
						r = self.send_command(com)
					elif self.event == '-0-' or self.event == '-1-' or self.event == '-2-' or self.event == '-3-' or self.event == '-4-' or self.event == '-5-' or self.event == '-6-' or self.event == '-7-' or self.event == '-8-' or self.event == '-9-' or self.event == '-10-':
						val = self.values[self.event]
						ret = update_info(val)
						print ("Update info fields result:", ret)
					elif self.event == '-SET_ACTIVE-':
						info['isactive'] = int(self.values[self.event])
						self.pbdl_win['-0-'].update(info['isactive'])
					elif self.event == 'View Downloader':
						self.create_downloader()
					elif self.event  == '2 Status':
						print (self.send_command('nordvpn status'))
					elif self.event == '0 Off':
						print(self.send_command('nordvpn disonnect'))
					elif self.event == '1 On':
						self.enable_vpn()
						print ("VPN Enabled!")
					else:
						print (self.event, self.values)
						pass

if __name__ == "__main__":
	pbdl = pbdl()
	#pbdl.create_window()
	#pbdl.create_downloader()
	pbdl.torrents = pbdl.build_torrent_data()
	print (pbdl.torrents)
	#pbdl.run()
