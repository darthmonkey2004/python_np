import pickle
from np.utils.pbdl.dl_missing import *
from np.core.gui import file_browse_window
import PySimpleGUI as sg
import os


class downloader():
	def __init__(self):
		self.data = {}
		self.seasons = []
		self.episode_numbers = []
		self.episode_names = []
		self.magnet = None
		self.magnet_data = {}
		self.indexes = []
		self.series_names = []
		self.tmdbids = []
		self.datfile = os.path.join(os.path.expanduser("~"), '.np', 'downloads.dat')
		try:
			self.dl_data = self.load_downloads(self.datfile)
			self.indexes, self.series_names, self.tmdbids = self.sort_dict(self.dl_data)
		except Exception as e:
			print(f"Couldn't parse data in '{self.datfile}'! ({e})")
			self.dl_data = []
			self.indexes, self.series_names, self.tmdbids = [], [], []
		self.keys = ['series_name', 'tmdbid', 'season', 'episode_number', 'episode_name']
		self.tmdbid = None
		self.series_name = None
		self.index = None
		self.indexs = []
		self.selected_data = None
		self.season = None
		self.episode_number = None
		self.episode_name = None
		self.selected_data = []
		self.window_conf = os.path.join(os.path.expanduser("~"), '.np', 'pbdl_window.dat')
		self.win = self.dl_manager()
		#self.start()

	def sort_dict(self, dl_data=None):
		if dl_data is not None:
			self.dl_data = dl_data
		pos = -1
		for line in self.dl_data:
			pos += 1
			self.indexes.append(pos)
			if line['series_name'] not in self.series_names:
				self.series_names.append(line['series_name'])
			if line['tmdbid'] not in self.tmdbids:
				self.tmdbids.append(line['tmdbid'])
		return self.indexes, self.series_names, self.tmdbids


	def tmdbid_to_series_name(self, tmdbid=None, dl_data=None):
		if tmdbid is not None:
			self.tmdbid = str(tmdbid)
		if dl_data is not None:
			self.dl_data = self.load_downloads()
		self.series_name = self.series_names[self.tmdbids.index(self.tmdbid)]
		return self.series_name

	def series_name_to_tmdbid(self, series_name=None, dl_data=None):
		if series_name is not None:
			self.series_name = series_name
		if dl_data is not None:
			self.dl_data = dl_data
		self.tmdbid = self.tmdbids[self.series_names.index(self.series_name)]
		return self.tmdbid

	def save_downloads(self, dl_data=None, datfile=None):
		if dl_data is not None:
			self.dl_data = dl_data
		if datfile is not None:
			self.datfile = datfile
		with open(self.datfile, 'wb') as f:
			pickle.dump(self.dl_data, f)
			f.close()

	def load_downloads(self, datfile=None):
		if datfile is not None:
			self.datfile = datfile
		if os.path.exists(self.datfile):
			with open(self.datfile, 'rb') as f:
				self.dl_data = pickle.load(f)
				f.close()
		else:
			print("File doesn't exist!", self.datfile)
			self.dl_data = {}
		return self.dl_data



	def update(self):
		self.data = self.get_filters()
		for key in self.data.keys():
			k = f"-{key}-"
			k = k.upper()
			list_key = f"{key}s"
			print(f"k:{k}, list_key:{list_key}")
			self.win[k].update(self.data[key], self.__dict__[list_key])
		d = self.filter(self.data)
		self.win['-DL_DATA-'].update(d)
		
	def get_filters(self):
		keys = ['-INDEX-', '-SERIES_NAME-', '-TMDBID-', '-SEASON-', '-EPISODE_NAME-', '-EPISODE_NAME-']
		data = {}
		for key in keys:
			try:
				val = self.win[key].get()
				if val == '':
					val = None
				if key == '-SERIES_NAME-':
					data['tmdbid'] = self.series_name_to_tmdbid(val)
				elif key == '-TMDBID-':
					data['series_name'] = self.tmdbid_to_series_name(val)
			except:
				val = None
			if val is not None:
				key = key.split('-')[1].lower()
				data[key] = val
		return data

	def parse(self, key, val, data=None):
		out = []
		self.seasons = []
		self.episode_numbers = []
		self.episode_names = []
		if data is None:
			data = self.dl_data
		for line in data:
			season = line['season']
			episode_number = line['episode_number']
			episode_name = line['episode_name']
			if season not in self.seasons:
				self.seasons.append(season)
			if episode_number not in self.episode_numbers:
				self.episode_numbers.append(episode_number)
			elif episode_name not in self.episode_names:
				self.episode_names.append(episode_name)
			try:
				del line['magnet_data']
			except:
				pass
			if str(val) == line[key]:
				if line not in out:
					out.append(line)
		return out
	
	

	def filter(self, data):
		keys = list(data.keys())
		vals = {}
		if 'episode_name' in keys:
			skey = 'episode_name'
			vals[skey] = data[skey]
		elif 'episode_number' in keys:
			skey = 'episode_number'
			vals[skey] = data[skey]
		else:
			skey = None
		if 'season' in keys:
			mkey = 'season'
			vals[mkey] = data[mkey]
		else:
			mkey = None
		if 'tmdbid' in keys:
			akey = 'tmdbid'
			vals[akey] = data[akey]
		elif 'series_name' in keys:
			akey = 'series_name'
			vals[akey] = data[akey]
		else:
			akey = None
		out = []
		if akey is not None:
			val = data[akey]
			out = self.parse(akey, val)
			print(len(out))
		if mkey is not None:
			val = data[mkey]
			out = self.parse(key=mkey, val=val, data=out)
			print(len(out))
		if skey is not None:
			val = data[skey]
			out = self.parse(key=skey, val=val, data=out)
			print(len(out))
		return out

	def dl_manager(self, datfile=None, window_title='Import/Export Downloads', dl_data={}):
		if datfile is not None:
			self.datfile = datfile
		layout = []
		output_line = [sg.Text('', key='-OUTPUT-')]
		fname_line = [sg.Input(default_text=self.datfile, enable_events=True, change_submits=True, do_not_clear=True, key='-FILEPATH-', expand_x=True), sg.Button(button_text='Browse...', auto_size_button=True, pad=(1, 1), key='-FILE_BROWSE-'), sg.Button(button_text='Save', auto_size_button=True, pad=(1, 1), key='-FILE_SAVE-'), sg.Button(button_text='Load', auto_size_button=True, pad=(1, 1), key='-FILE_LOAD-')]
		dropdowns = [sg.Text('Line Number:'), sg.Combo(self.indexes, self.index, enable_events=True, key='-INDEX-'), sg.Text('Series Name:'), sg.Combo(self.series_names, self.series_name, enable_events=True,key='-SERIES_NAME-'), sg.Text('TMDB Id:'), sg.Combo(self.tmdbids, self.tmdbid, enable_events=True,key='-TMDBID-'), sg.Text('Season:'), sg.Combo(self.seasons, self.season, enable_events=True,key='-SEASON-'), sg.Text('Episode Number:'), sg.Combo(self.episode_numbers, self.episode_number, enable_events=True,key='-EPISODE_NUMBER-'), sg.Text('Episode Name:'), sg.Combo(self.episode_names, self.episode_name, enable_events=True,key='-EPISODE_NAME-'), sg.Button('Clear!', key='-CLEAR-')]
		data_box = [sg.Listbox(values=self.selected_data, change_submits=True, size = (200, 10), auto_size_text=False, enable_events=True, expand_x=False, expand_y=False, key='-DL_DATA-')]
		buttons = [sg.Button('Scan!', key='-SCAN-'), sg.Button(button_text='Add', key='-ADD-'), sg.Button(button_text='Remove', key='-REMOVE-'), sg.Button(button_text='Download!', key='-DOWNLOAD-'), sg.Button(button_text='Close', key='-CLOSE-')]
		layout.append(fname_line)
		layout.append(dropdowns)
		layout.append(data_box)
		layout.append(output_line)
		layout.append(buttons)
		self.win = sg.Window(window_title, layout, keep_on_top=False, element_justification='center', finalize=True)
		self.size, self.location = self.load_window_dims()
		self.win.size = self.size
		x, y = self.location
		self.win.move(x, y)
		return self.win

	def start(self):
		self.loop()

	def stop(self):
		self.runloop = False

	def exit(self):
		self.stop()
		self.store_window_dims()
		self.win.close()

	def store_window_dims(self):
		self.size = self.win.size
		self.location = self.win.current_location()
		with open(self.window_conf, 'wb') as f:
			pickle.dump((self.size, self.location), f)
			f.close()
		return self.size, self.location

	def load_window_dims(self):
		if not os.path.exists(self.window_conf):
			self.size, self.location = self.store_window_dims()
		try:
			with open(self.window_conf, 'rb') as f:
				self.size, self.location = pickle.load(f)
				f.close()
		except:
			self.size, self.location = self.store_window_dims()
		return self.size, self.location


	def loop(self):
		self.runloop = True
		while self.runloop:
			self.event, self.values = self.win.read()
			if self.event == sg.WIN_CLOSED:
				break
			elif self.event == '-CLOSE-':
				self.exit()
				break
			elif self.event == '-FILE_LOAD-':
				self.datfile = self.values['-FILEPATH-']
				self.dl_data = self.load_downloads(self.datfile)
				self.indexes, self.series_names, self.tmdbids = self.sort_dict(self.dl_data)
				self.win['-INDEX-'].update(self.indexes)
				self.win['-SERIES_NAME-'].update(self.series_names)
				self.win['-TMDBID-'].update(self.tmdbids)
				self.win['-OUTPUT-'].update("Data loaded!")
			elif self.event == '-FILE_SAVE-':
				self.datfile = self.values['-FILEPATH-']
				self.save_downloads(datfile=self.datfile, dl_data=self.dl_data)
				self.win['-OUTPUT-'].update(f"Data saved!")
			elif self.event == '-FILE_BROWSE-':
				self.datfile = self.file_browse_window()
				self.win['-OUTPUT-'].update(f"File selected:{self.datfile}!")
				self.win['-FILEPATH-'].update(self.datfile)
			elif self.event == '-SCAN-':
				self.dl_data = get_downloads()
				self.win['-OUTPUT-'].update('Scan complete! Data loaded')
			elif self.event == '-INDEX-':
				self.index = self.values[self.event]
				d = self.dl_data[self.index]
				self.series_name = d['series_name']
				self.tmdbid = d['tmdbid']
				self.season = d['season']
				self.episode_number = d['episode_number']
				self.episode_name = d['episode_name']
				self.magnet_data = d['magnet_data']
				self.update()
			elif self.event == '-SERIES_NAME-':
				self.series_name = self.values[self.event]
				self.update()
			elif self.event == '-TMDBID-':
				self.series_name = self.values[self.event]
				self.update()
			elif self.event == '-SEASON-':
				self.season = int(self.values[self.event])
				self.update()
			elif self.event == '-EPISODE_NUMBER-':
				self.episode_number = int(self.values[self.event])
				self.update()
			elif self.event == '-EPISODE_NAME-':
				self.episode_name = int(self.values[self.event])
				self.update()
			elif self.event == '-CLEAR-':
				self.indexes, self.series_names, self.tmdbids = self.sort_dict(self.dl_data)
				self.win['-INDEX-'].update(None, self.indexes)
				self.win['-SERIES_NAME-'].update(None, self.series_names)
				self.win['-TMDBID-'].update(None, self.tmdbids)
				self.win['-SEASON-'].update(None, self.seasons)
				self.win['-EPISODE_NUMBER-'].update(None, self.episode_numbers)
				self.win['-EPISODE_NAME-'].update(None, self.episode_names)
			else:
				try:
					vals = self.values[self.event]
				except Exception as e:
					print(f"Failed to get values for event {self.event}!")
					vals = None
				print(f"Unhandled event:{self.event}, values:{vals}")
		print("loop exited!")
