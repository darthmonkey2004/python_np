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
		self.series_names = []
		self.tmdbids = []
		self.last_clicked = None
		self.datfile = os.path.join(os.path.expanduser("~"), '.np', 'downloads.dat')
		try:
			self.dl_data = self.load_downloads(self.datfile)
			self.series_names, self.tmdbids, self.seasons, self.episode_numbers, self.episode_names = self.sort_dict(self.dl_data)
		except Exception as e:
			print(f"Couldn't parse data in '{self.datfile}'! ({e})")
			self.dl_data = []
			self.series_names, self.tmdbids = [], []
		self.keys = ['series_name', 'tmdbid', 'season', 'episode_number', 'episode_name']
		self.tmdbid = None
		self.series_name = None
		self.selected_data = None
		self.season = None
		self.episode_number = None
		self.episode_name = None
		self.selected_data = []
		self.window_conf = os.path.join(os.path.expanduser("~"), '.np', 'pbdl_window.dat')
		self.win = self.dl_manager()
		self.auto = True
		self.win['-AUTOPICK_MAGNET-'].update(self.auto)
		self.start()

	def sort_dict(self, dl_data=None):
		if dl_data is not None:
			self.dl_data = dl_data
		for line in self.dl_data:
			if line['series_name'] not in self.series_names:
				self.series_names.append(line['series_name'])
			if line['tmdbid'] not in self.tmdbids:
				self.tmdbids.append(line['tmdbid'])
			if line['season'] not in self.seasons:
				self.seasons.append(line['season'])
			if line['episode_number'] not in self.episode_numbers:
				self.episode_numbers.append(line['episode_number'])
			if line['episode_name'] not in self.episode_names:
				self.episode_names.append(line['episode_name'])
		return self.series_names, self.tmdbids, self.seasons, self.episode_numbers, self.episode_names


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

	def _filter(self, key, val, data=None):
		if data is None:
			data = self.dl_data
		out = []
		for line in data:
			if str(line[key]) == str(val):
				#print(line[key], val)
				out.append(line)
		return out


	def filter(self, data=None, filters=None):
		if filters is None:
			filters = self.get_filters()
		if data is None:
			data = self.dl_data
		for key in filters.keys():
			data = self._filter(key, filters[key], data)
		return data


	def remove(self, key, val, data=None):
		if key == '-SERIES_NAMES-' or key == '-SERIES_NAME-':
			key = 'series_name'
		elif key == '-TMDBIDS-' or key == '-TMDBID-':
			key = 'tmdbid'
		elif key == '-SEASONS-' or key == '-SEASON-':
			key = 'season'
		elif key == '-EPISODE_NUMBERS-' or key == '-EPISODE_NUMBER-':
			key = 'episode_number'
		elif key == '-EPISODE_NAMES-' or key == '-EPISODE_NAME-':
			key = 'episode_name'
		out = []
		if data is None:
			data = self.dl_data
		for line in data:
			try:
				if type(val) == list:
					val = val[0]
				print(f"remove - key:{key}, val:{val}")
				if str(val) == str(line[key]):
					#print("skipping:", val, key)
					pass
				else:
					out.append(line)
			except Exception as e:
				print("Failed to remove item ({e}):", line)
				out.append(line)
		self.data = out
		self.populate_data(self.data)
		return self.data


	def fill_fields(self, data=None):
		if data is None:
			data = self.dl_data
		self.series_names = []
		self.tmdbids = []
		self.seasons = []
		self.episode_numbers = []
		self.episode_names = []
		for line in data:
			if line['series_name'] not in self.series_names:
				self.series_names.append(line['series_name'])
			if line['tmdbid'] not in self.tmdbids:
				self.tmdbids.append(line['tmdbid'])
			if line['season'] not in self.seasons:
				self.seasons.append(line['season'])
			if line['episode_number'] not in self.episode_numbers:
				self.episode_numbers.append(line['episode_number'])
			if line['episode_name'] not in self.episode_names:
				self.episode_names.append(line['episode_name'])
		if len(self.series_names) == 1:
			self.series_name = self.series_names[0]
		if len(self.tmdbids) == 1:
			self.tmdbid = self.tmdbids[0]
		if len(self.seasons) == 1:
			self.season = self.seasons[0]
		if len(self.episode_numbers) == 1:
			self.episode_number = self.episode_numbers[0]
		if len(self.episode_names) == 1:
			self.episode_name = self.episode_names[0]
		self.win['-SERIES_NAME-'].update(self.series_name, self.series_names)
		self.win['-TMDBID-'].update(self.tmdbid, self.tmdbids)
		self.win['-SEASON-'].update(str(self.season), self.seasons)
		self.win['-EPISODE_NUMBER-'].update(self.episode_number, self.episode_numbers)
		self.win['-EPISODE_NAME-'].update(self.episode_name, self.episode_names)
		self.populate_data(data)


	def clear_item(self, key):
		series_names, tmdbids, seasons, episode_numbers, episode_names = self.sort_dict()
		if key == '-SERIES_NAMES-' or key == '-SERIES_NAME-':
			self.series_name = None
			self.win['-SERIES_NAME-'].update(self.series_name, series_names)
			self.win['-SERIES_NAMES-'].update(series_names)
		elif key == '-TMDBIDS-' or key == '-TMDBID-':
			self.tmdbid = None
			self.win['-TMDBID-'].update(self.tmdbid, tmdbids)
			self.win['-TMDBIDS-'].update(tmdbids)
		elif key == '-SEASONS-' or key == '-SEASON-':
			self.season = None
			self.win['-SEASON-'].update(self.season, seasons)
			self.win['-SEASONS-'].update(seasons)
		elif key == '-EPISODE_NUMBERS-' or key == '-EPISODE_NUMBER-':
			self.episode_number = None
			self.win['-EPISODE_NUMBER-'].update(self.episode_number, episode_numbers)
			self.win['-EPISODE_NUMBERS-'].update(episode_number)
		elif key == '-EPISODE_NAMES-' or key == '-EPISODE_NAME-':
			self.episode_name = None
			self.win['-EPISODE_NAME-'].update(self.episode_name, episode_names)
			self.win['-EPISODE_NAMES-'].update(episode_name)


	def update(self):
		self.fill_fields(self.filter())

		
	def get_filters(self):
		keys = ['-SERIES_NAME-', '-TMDBID-', '-SEASON-', '-EPISODE_NUMBER-', '-EPISODE_NAME-']
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
		#print(f"filters:{data}")
		return data


	def dl_manager(self, datfile=None, window_title='Import/Export Downloads', dl_data={}):
		if datfile is not None:
			self.datfile = datfile
		layout = []
		output_line = [sg.Text('', key='-OUTPUT-')]
		fname_line = [sg.Input(default_text=self.datfile, enable_events=True, change_submits=True, do_not_clear=True, key='-FILEPATH-', expand_x=True), sg.Button(button_text='Browse...', auto_size_button=True, pad=(1, 1), key='-FILE_BROWSE-'), sg.Button(button_text='Save', auto_size_button=True, pad=(1, 1), key='-FILE_SAVE-'), sg.Button(button_text='Load', auto_size_button=True, pad=(1, 1), key='-FILE_LOAD-'), sg.Button('Clear!', key='-CLEAR-')]
		dropdowns = [sg.Text('Series Name:'), sg.Combo(self.series_names, self.series_name, enable_events=True,key='-SERIES_NAME-'), sg.Text('TMDB Id:'), sg.Combo(self.tmdbids, self.tmdbid, enable_events=True,key='-TMDBID-'), sg.Text('Season:'), sg.Combo(self.seasons, self.season, enable_events=True,key='-SEASON-'), sg.Text('Episode Number:'), sg.Combo(self.episode_numbers, self.episode_number, enable_events=True,key='-EPISODE_NUMBER-'), sg.Text('Episode Name:'), sg.Combo(self.episode_names, self.episode_name, enable_events=True,key='-EPISODE_NAME-')]
		#data_boxes = [sg.Listbox(values=self.selected_data, change_submits=True, size = (35, 10), auto_size_text=False, enable_events=True, expand_x=False, expand_y=False, key='-DL_DATA-')]
		data_boxes = [sg.Listbox(values=[], change_submits=True, size = (35, 10), auto_size_text=False, enable_events=True, expand_x=False, expand_y=False, key='-SERIES_NAMES-'), sg.Listbox(values=[], change_submits=True, size = (35, 10), auto_size_text=False, enable_events=True, expand_x=False, expand_y=False, key='-TMDBIDS-'), sg.Listbox(values=[], change_submits=True, size = (35, 10), auto_size_text=False, enable_events=True, expand_x=False, expand_y=False, key='-SEASONS-'), sg.Listbox(values=[], change_submits=True, size = (35, 10), auto_size_text=False, enable_events=True, expand_x=False, expand_y=False, key='-EPISODE_NUMBERS-'), sg.Listbox(values=[], change_submits=True, size = (35, 10), auto_size_text=False, enable_events=True, expand_x=False, expand_y=False, key='-EPISODE_NAMES-')]
		magnet_box = [sg.Listbox(values=[], change_submits=True, size = (200, 10), auto_size_text=False, enable_events=True, expand_x=False, expand_y=False, key='-MAGNET_DATA-')]
		buttons = [sg.Button('Stop loop!', key='-STOP_LOOP-'), sg.Checkbox(text="Magnet Auto-Select:", auto_size_text=True, change_submits=True, enable_events=True, key='-AUTOPICK_MAGNET-'), sg.Button('Scan!', key='-SCAN-'), sg.Button('Get Downloads!', key='-GET_DOWNLOADS-'), sg.Button(button_text='Add', key='-ADD-'), sg.Button(button_text='Remove', key='-REMOVE-'), sg.Button(button_text='Download!', key='-DOWNLOAD-'), sg.Button(button_text='Close', key='-CLOSE-')]
		layout.append(fname_line)
		layout.append(dropdowns)
		layout.append(data_boxes)
		layout.append(magnet_box)
		layout.append(output_line)
		layout.append(buttons)
		self.win = sg.Window(window_title, layout, keep_on_top=False, element_justification='center', finalize=True)
		self.size, self.location = self.load_window_dims()
		#self.win.size = self.size
		self.win.size = 1400, 450
		x, y = self.location
		self.win.move(x, y)
		return self.win

	def populate_data(self, data=None):
		if data is None:
			data = self.dl_data
		series_names = []
		tmdbids = []
		seasons = []
		episode_numbers = []
		episode_names = []
		magnets = []
		m = []
		for line in data:
			if line['series_name'] not in series_names:
				series_names.append(line['series_name'])
			if line['tmdbid'] not in tmdbids:
				tmdbids.append(line['tmdbid'])
			if line['season'] not in seasons:
				seasons.append(line['season'])
			if line['episode_number'] not in episode_numbers:
				episode_numbers.append(line['episode_number'])
			if line['episode_name'] not in episode_names:
				episode_names.append(line['episode_name'])
			m.append(line['magnet_data'])
		for item in m:
			if item is not None:
				magnets += list(item.keys())
		self.win['-SERIES_NAMES-'].update(series_names)
		self.win['-TMDBIDS-'].update(tmdbids)
		self.win['-SEASONS-'].update(seasons)
		self.win['-EPISODE_NUMBERS-'].update(episode_numbers)
		self.win['-EPISODE_NAMES-'].update(episode_names)
		self.win['-MAGNET_DATA-'].update(magnets)

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

	def listbox_handler(self, event, val=None):
		try:
			val = self.values[self.event][0]
		except Exception as e:
			val = None
		if val is not None:
			if val == self.series_name:
				pass
			else:
				key = event.split('-')[1].lower()
				l = len(key) - 1
				key = key[:l]
				self.__dict__[key] = val
				print(f"Updated: key={key}, val={val}")
				self.update()


	def loop(self):
		listbox_keys = ['-SERIES_NAMES-', '-TMDBIDS-', '-SEASONS-', '-EPISODE_NUMBERS-', '-EPISODE_NAMES-']
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
				self.series_names, self.tmdbids, self.seasons, self.episode_numbers, self.episode_names = self.sort_dict(self.dl_data)
				self.series_name = None
				self.tmdbid = None
				self.season = None
				self.episode_number = None
				self.episode_name = None
				self.win['-SERIES_NAME-'].update(self.series_name, self.series_names)
				self.win['-TMDBID-'].update(self.tmdbid, self.tmdbids)
				self.win['-SEASON-'].update(self.season, self.seasons)
				self.win['-EPISODE_NUMBER-'].update(self.episode_number, self.episode_numbers)
				self.win['-EPISODE_NAME-'].update(self.episode_name, self.episode_names)
				self.populate_data(self.dl_data)
			elif self.event == '-FILE_SAVE-':
				self.datfile = self.values['-FILEPATH-']
				self.save_downloads(datfile=self.datfile, dl_data=self.dl_data)
				self.win['-OUTPUT-'].update(f"Data saved!")
			elif self.event == '-FILE_BROWSE-':
				self.datfile = self.file_browse_window()
				self.win['-OUTPUT-'].update(f"File selected:{self.datfile}!")
				self.win['-FILEPATH-'].update(self.datfile)
			elif self.event == '-SCAN-':
				self.dl_data = get_dict()
				self.win['-OUTPUT-'].update('Scan complete! Data loaded')
				self.update()
			elif self.event == '-SERIES_NAME-':
				self.series_name = self.values[self.event]
				self.update()
			elif self.event == '-TMDBID-':
				self.tmdbid = self.values[self.event]
				self.update()
			elif self.event == '-SEASON-':
				self.season = int(self.values[self.event])
				self.update()
			elif self.event == '-EPISODE_NUMBER-':
				self.episode_number = int(self.values[self.event])
				self.update()
			elif self.event == '-EPISODE_NAME-':
				self.episode_name = self.values[self.event]
				self.update()
			elif self.event == '-CLEAR-':
				self.series_names, self.tmdbids, self.seasons, self.episode_numbers, self.episode_names = self.sort_dict(self.dl_data)
				self.series_name = None
				self.tmdbid = None
				self.season = None
				self.episode_number = None
				self.episode_name = None
				self.win['-SERIES_NAME-'].update(self.series_name, self.series_names)
				self.win['-TMDBID-'].update(self.tmdbid, self.tmdbids)
				self.win['-SEASON-'].update(self.season, self.seasons)
				self.win['-EPISODE_NUMBER-'].update(self.episode_number, self.episode_numbers)
				self.win['-EPISODE_NAME-'].update(self.episode_name, self.episode_names)
				self.populate_data(self.dl_data)
			elif self.event in listbox_keys:
				print("Sending to listbox handler:", self.event, self.values[self.event])
				self.listbox_handler(self.event, self.values[self.event])
			elif self.event == '-GET_DOWNLOADS-':
				self.win['-OUTPUT-'].update(f"Finding downloads for selected items...")
				self.dl_data = get_downloads(self.dl_data)
				self.win['-OUTPUT-'].update(f"Done! Updating...")
				self.update()
			elif self.event == '-MAGNET_DATA-':
				self.magnet = None
				self.magnet_name = self.values[self.event]
				if type(self.magnet_name) == list:
					self.magnet_name = self.magnet_name[0]
				self.last_clicked = self.event, self.magnet_name
				print(f"last_clicked set: {self.last_clicked}")
				for line in self.dl_data:
					magdata = list(line['magnet_data'].keys())
					if self.magnet_name in magdata:
						idx = magdata.index(self.magnet_name)
						self.magnet = list(line['magnet_data'].values())[idx]
						#print(f"Magnet selected! Name:{self.magnet_name}, idx:{idx}, magnet:{self.magnet}")
						break
			elif self.event == '-REMOVE-':
				if self.last_clicked is not None:
					key, val = self.last_clicked
					if key == '-MAGNET_DATA-':
						for line in self.dl_data:
							magdata = list(line['magnet_data'].keys())
							if self.magnet_name in magdata:
								del line['magnet_data'][self.magnet_name]
					else:
						self.dl_data = self.remove(key, val)
					self.update()
			elif self.event == '-AUTOPICK_MAGNET-':
				self.auto = self.values[self.event]
				print("Automatic downloading toggled! (value:{self.auto})")
			elif self.event == '-DOWNLOAD-':
				download(data=self.dl_data, auto=self.auto)
			elif self.event == '-STOP_LOOP-':
				break
			else:
				print(f"Unhandled event:{self.event}")
			try:
				self.last_clicked = self.event, self.values[self.event]
				print(f"last_clicked set: {self.last_clicked}")
			except:
				try:
					self.last_clicked = self.event, self.win[self.event].get()
					print(f"last_clicked set: {self.last_clicked}")
				except:
					self.last_clicked = self.event, None
					print(f"last_clicked set: {self.last_clicked}")
		print("loop exited!")

if __name__ == "__main__":
	d = downloader()
