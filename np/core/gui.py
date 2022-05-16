import os
import np
import PySimpleGUI as sg
#-----------main gui creation class------------#
class gui():
	def __init__(self):
		self.TAB = '-player_control_layout-'
		self.RESET = False
		self.win_type = 'internal'
		self.player = np.nplayer()
		self.media = self.player.create_media()
		self.conf = np.readConf()
		self.conf['gui_data'] = {}
		self.tables = ['series', 'movies', 'music']
		self.theme = 'DarkBlue'
		self.play_type = self.conf['play_type']
		if self.conf['screen'] == 0:
			scrnbtn0_val = True
			scrnbtn1_val = False
		elif self.conf['screen'] == 1:
			scrnbtn0_val = False
			scrnbtn1_val = True
		self.conf['windows'] = np.init_window_position()
		state = self.conf['windows']['visible_state']
		screen = self.conf['screen']
		self.gui_win_x = self.conf['windows']['gui'][state][screen]['x']
		self.gui_win_y = self.conf['windows']['gui'][state][screen]['y']
		self.gui_win_w = self.conf['windows']['gui'][state][screen]['w']
		self.gui_win_h = self.conf['windows']['gui'][state][screen]['h']
		self.viewer_win_x = self.conf['windows']['viewer'][screen]['x']
		self.viewer_win_y = self.conf['windows']['viewer'][screen]['y']
		self.viewer_win_w = self.conf['windows']['viewer'][screen]['w']
		self.viewer_win_h = self.conf['windows']['viewer'][screen]['h']
		self.window = None
		self.event = None
		self.values = None
		self.player_window_layout = []
		self.uievent = None
		self.uivalues = {}
		self.window = None
		self.table = self.conf['play_type']
		self.isactive = True
		self.dbmgr_picked_items = []
		self.pbdl_dl_win = None
		if self.conf['play_type'] == 'videos':
			self.table = 'series'
		sg.theme(self.theme)
		self.WINDOW = self.create_gui_window()
		if self.win_type == 'internal':
			self.WINDOW2 = sg.Window('Viewer', self.player_window_layout, no_titlebar=True, location=(int(self.viewer_win_x), int(self.viewer_win_y)), size=(int(self.viewer_win_w), int(self.viewer_win_h)), grab_anywhere=True, keep_on_top=False, element_justification='center', finalize=True, resizable=True).Finalize()
			self.WINDOW2['-VID_OUT-'].expand(True, True)
		self.RESET = False


	def create_gui_window(self):
		line = []
		scale = float(int(self.conf['scale']) * 10)
		control_modes = self.conf['network_modes']['control_modes']
		media_modes = self.conf['network_modes']['media_modes']
		search_line = [self.create_old('dropdown_menu', [self.tables, self.conf['play_type'], '-PLAY_TYPE-']), self.create_old('dropdown_menu', [list(self.conf['screens'].keys()), self.conf['screen'], '-SET_SCREEN-']), self.create_old('dropdown_menu', [['database', 'playlist'], 'database', '-PLAY_MODE-']), self.create_old('dropdown_menu', [control_modes, self.conf['network_mode']['control_mode'], '-CONTROL_MODE-']), self.create_old('dropdown_menu', [media_modes, self.conf['network_mode']['media_mode'], '-MEDIA_MODE-']), self.create_old('textbox', ['Search', '-SEARCH-']), self.create_old('text_input', ['Enter search query:', '-SEARCH_QUERY-']), self.create_old('btn', ['Search', 'Search'])]
		elem_media_list = [self.create_old('listbox', [self.media['DBMGR_RESULTS'], '-CURRENT_PLAYLIST-'])]
		update_line = [self.create_old('btn', ['Refresh from Database'])]
		player_controls1 = [self.create_old('btn', ['Volume Up']), self.create_old('btn', ['previous']), self.create_old('btn', ['play']), self.create_old('btn', ['next']), self.create_old('btn', ['pause']), self.create_old('btn', ['stop'])]
		player_controls2 = [self.create_old('btn', ['Volume Down']), self.create_old('btn', ['seek fwd']), self.create_old('btn', ['seek rev']), self.create_old('btn', ['Exit']), self.create_old('btn', ['Screenshot'])]
		try:
			play_pos = float(self.conf['nowplaying']['play_pos'])
		except:
			play_pos = 0
			self.conf['nowplaying']['play_pos'] = play_pos
		slider_scale = [sg.Slider(range=(0,1), resolution=0.01, default_value=play_pos, orientation='h', expand_x = True, enable_events = True, change_submits = True, key='-PLAY_POS-')]
		line_window_ctl = [self.create_old('btn', ['store window location']), self.create_old('btn', ['Hide UI']), self.create_old('btn', ['Recenter UI']), self.create_old('btn', ['Fix Focus'])]
		self.video_temp_img = self.create_old('image', [np.DEFAULT_POSTER, '-VID_OUT-'])
		
		line.append(self.video_temp_img)
		
		self.player_window_layout.append(line)
		self.player_window_layout.append([sg.Sizegrip(key='-viewer_size-')])
		if self.play_type == 'movies':
			columns_list = ['id', 'isactive', 'tmdbid', 'title', 'year', 'release_date', 'duration', 'description', 'poster', 'filepath', 'md5', 'url']
			radio_sql_table_select = [[sg.Radio('series', "TABLES", default=False, enable_events=True, key='-table_series-'), sg.Radio('movies', "TABLES", default=True, enable_events=True, key='-table_movies-'), sg.Radio('music', "TABLES", default=False, enable_events=True, key='-table_music-'), self.create_old('btn', ['Select All', '-Select All-']), self.create_old('btn', ['Clear All', '-Clear All-'])]]
		elif self.play_type == 'series' or self.play_type == 'videos':
			columns_list = ['id', 'isactive', 'series_name', 'tmdbid', 'season', 'episode_number', 'episode_name', 'description', 'air_date', 'still_path', 'duration', 'filepath', 'md5', 'url']
			radio_sql_table_select = [[sg.Radio('series', "TABLES", default=True, enable_events=True, key='-table_series-'), sg.Radio('movies', "TABLES", default=False, enable_events=True, key='-table_movies-'), sg.Radio('music', "TABLES", default=False, enable_events=True, key='-table_music-'), self.create_old('btn', ['Select All', '-Select All-']), self.create_old('btn', ['Clear All', '-Clear All-'])]]
		elif self.play_type == 'music':
			columns_list = ['id', 'isactive', 'title', 'accoustic_id', 'album', 'album_id', 'artist_id', 'year', 'artist', 'track', 'track_ct', 'filepath']
			radio_sql_table_select = [[sg.Radio('series', "TABLES", default=False, enable_events=True, key='-table_series-'), sg.Radio('movies', "TABLES", default=False, enable_events=True, key='-table_movies-'), sg.Radio('music', "TABLES", default=True, enable_events=True, key='-table_music-'), self.create_old('btn', ['Select All', '-Select All-']), self.create_old('btn', ['Clear All', '-Clear All-'])]]
		radio_frame = sg.Frame(title='', layout=radio_sql_table_select, key='table_select', expand_x=True, grab=True, element_justification="left", vertical_alignment="top")
		self.player_control_layout = [
			search_line,
			elem_media_list,
			update_line,
			[sg.Input(default_text='Video URL or Local Path:', size=(30, 1), expand_x=True, key='-VIDEO_LOCATION-'), sg.Button('load')],
			player_controls1,
			player_controls2,
			slider_scale,
			[sg.Text('Load media to start', key='-MESSAGE_AREA-')],
			line_window_ctl,
			[]
		]
		dbitems = []
		listbox_dbitems = [[sg.Listbox(columns_list, size=(20, 10), select_mode='multiple', change_submits=True, auto_size_text=True, enable_events=True, key='-DBMGR_PICKED_COLUMNS-'), sg.Listbox(dbitems, size=(70, 10), select_mode='multiple', change_submits=True, auto_size_text=True, expand_x=True, enable_events=True, key='-DBMGR_RESULTS-'), sg.Listbox(self.dbmgr_picked_items, size=(20, 10), select_mode='multiple', change_submits=True, auto_size_text=True, enable_events=True, key='-DBMGR_SELECTED_ROWS-')]]
		listbox_dbitems = sg.Frame(title='', layout=listbox_dbitems, key='listbox_dbitems', expand_x=True, grab=True, element_justification="left", vertical_alignment="top")
		#ckbox_is_active = [self.create_old('checkbox', ['Active:', '-setactive-'])]
		btn_update_info = [self.create_old('btn', ['Query TMDB', '-Query TMDB-']), self.create_old('btn', ['Read Info', '-Read Info-']), self.create_old('btn', ['Update Info', '-Update Info-']), self.create_old('btn', ['Set Active', '-Set Active-']), self.create_old('btn', ['Set Inactive', '-Set Inactive-']), self.create_old('btn', ['Remove Selected', '-Remove Selected-'])]
		textinput_query_string = [[sg.Input(size=(30, 1), expand_x=True, enable_events=True, key='-DBMGR_QUERY_STRING-'), self.create_old('btn', ['SQL Search'])]]
		textinput_query_string = sg.Frame(title='', layout=textinput_query_string, key='textinput_query_string', expand_x=True, grab=True, element_justification="left", vertical_alignment="top")
		self.poster_img = [sg.Image(np.DEFAULT_POSTER, subsample=4, key='-poster_img-')]
		self.db_mgr_layout = [
			[radio_frame],
			[listbox_dbitems],
			[sg.Text()],
			[textinput_query_string],
			[sg.Text()],
		]
		cct = len(columns_list)
		cct = cct - 1
		pos = -1
		while pos != cct:
			pos = pos + 1
			column = columns_list[pos]
			pos = pos + 1
			column2 = columns_list[pos]
			text = (column + ":")
			key=("-" + column + "-")
			text2 = (column2 + ":")
			key2=("-" + column2 + "-")
			field = sg.Input(size=(30, 1), default_text=text, enable_events=True, expand_x=True, key=key), sg.Text(), sg.Input(size=(30,1), enable_events=True, default_text=text2, expand_x=True, key=key2)
			self.db_mgr_layout.append(field)
			text = None
			text2 = None
			key = None
			key2 = None
		#self.db_mgr_layout.append(ckbox_is_active)
		self.db_mgr_layout.append(btn_update_info)
		self.db_mgr_layout.append(self.poster_img)
		self.menu_def = [['&File', ['-&Load Directory-', '-&Load Playlist-', '-&Save Playlist-', 'E&xit']], ['&Tools', ['&Pirate Bay Downloader', '&Torrent Manager', '&youtube-dl', '&Video Filters', [np.VLC_VIDEO_FILTERS], '&Audio Filters', [np.VLC_AUDIO_FILTERS]]], ['&Help', '&About...']]

		self.layout = [[sg.MenubarCustom(self.menu_def, tearoff=True, key='-menubar_key-'), sg.Button("Close")], [sg.TabGroup([[sg.Tab('MP Controls', self.player_control_layout, key='-player_control_layout-')], [sg.Tab('DB Manager', self.db_mgr_layout, key='-db_mgr_layout-')]], expand_x=True, expand_y=True, enable_events=True)], [sg.Sizegrip(key='-gui_size-')]]

		self.WINDOW = sg.Window('GUI', self.layout, no_titlebar=True, location=(int(self.gui_win_x),int(self.gui_win_y)), size=(self.gui_win_w,self.gui_win_h), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
		return self.WINDOW


	def init_window_position(self):
		screen = self.conf['screen']
		self.conf['windows'] = np.init_window_position()
		np.writeConf(self.conf)
		return self.conf['windows']


	def get_window_location(self, window=None):
		if window == None:
			np.log(f"Error Getting Window location: Name=None, no name provided. Options are 'viewer/player', and 'gui'.", 'error')
			return False
		elif window == 'player' or window == 'viewer':
			try:
				coords = self.WINDOW2.CurrentLocation()
			except Exception as e:
				np.log(f"Error Getting Window location: Name={window} appears to be closed!", 'error')
				return None
		elif window == 'gui':
			try:
				coords = self.WINDOW.CurrentLocation()
			except Exception as e:
				np.log(f"Error Getting Window location: Name=appears to be closed!", 'error')
				return None
		np.log(f"Window location: Name={window}, Coords={coords}", 'info')
		return coords
	


	def move_window(self, window, x=None, y=None):
		try:
			state = self.conf['windows']['visible_state']
			screen = self.conf['screen']
			self.gui_win_w = self.conf['windows']['gui'][state][screen]['w']
			self.gui_win_h = self.conf['windows']['gui'][state][screen]['h']
			self.viewer_win_w = self.conf['windows']['viewer'][screen]['w']
			self.viewer_win_h = self.conf['windows']['viewer'][screen]['h']
		except:
			self.conf = np.readConf()
			state = self.conf['windows']['visible_state']
			screen = self.conf['screen']
			self.gui_win_w = self.conf['windows']['gui'][state][screen]['w']
			self.gui_win_h = self.conf['windows']['gui'][state][screen]['h']
			self.viewer_win_w = self.conf['windows']['viewer'][screen]['w']
			self.viewer_win_h = self.conf['windows']['viewer'][screen]['h']
		if x is None:
			if window == 'player' or window == 'viewer':
				self.viewer_win_x = self.conf['windows']['viewer'][screen]['x']
				self.WINDOW2.move(self.viewer_win_x, self.viewer_win_y)
			elif window == 'gui':
				self.gui_win_x = self.conf['windows']['gui'][state][screen]['x']
				self.WINDOW.move(self.gui_win_x , self.gui_win_y)
		else:
			if window == 'player' or window == 'viewer':
				self.viewer_win_x = x
				self.WINDOW2.move(self.viewer_win_x, self.viewer_win_y)
			elif window == 'gui':
				self.gui_win_x = x
				self.WINDOW.move(self.gui_win_x , self.gui_win_y)
		if y is None:
			if window == 'player' or window == 'viewer':
				self.viewer_win_y = self.conf['windows']['viewer'][screen]['y']
				self.WINDOW2.move(self.viewer_win_x, self.viewer_win_y)
			elif window == 'gui':
				self.gui_win_y = self.conf['windows']['gui'][state][screen]['y']
				self.WINDOW.move(self.gui_win_x , self.gui_win_y)
		else:
			if window == 'player' or window == 'viewer':
				self.viewer_win_y = y
				self.WINDOW2.move(self.viewer_win_x, self.viewer_win_y)
			elif window == 'gui':
				self.gui_win_y = y
				self.WINDOW.move(self.gui_win_x , self.gui_win_y)
		np.log(f"{window} window moved to!", 'info')
			
			
	def create(self, elem, args={}):
		pos = -1
		argdict = {}
		sig = inspect.signature(globals()[elem])
		sig_keys = list(sig.parameters.keys())
		for param in sig.parameters.values():
			pos = pos + 1
			key = sig_keys[pos]
			if param.default is param.empty and key not in list(args.keys()):
				raise Exception ('Required value not provided!', param, args, sig)
			elif param.default is not param.empty and key not in list(args.keys()):
				argdict[key] = param.default
			elif key in list(args.keys()):
				argdict[key] = args[key]
		vals_list = list(argdict.keys())
		vals = tuple(vals_list)
		element = globals()[elem](vals)
		return element


	def get_user_input(self, window_title='User Input'):
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
				self.user_input = values[event]
		return self.user_input


	def create_old(self, elem, args=[]):
		def dropdown_menu(args):
			return sg.Combo(args[0],default_value=args[1],enable_events=True,key=args[2])

		def textbox(args):
			return sg.Text(text=args[0], auto_size_text=True, enable_events=True, key=args[1])

		def text_input(args):
			return sg.Input(default_text=args[0], enable_events=True, do_not_clear=True, key=args[1], expand_x=True)

		def btn(args):
			try:
				key = str(args[1])
				return sg.Button(button_text=args[0], auto_size_button=True, pad=(1, 1), expand_x=True, key=key)
			except:
				return sg.Button(button_text=args[0], auto_size_button=True, pad=(1, 1), expand_x=True)


		def listbox(args):
			return sg.Listbox(values=args[0], change_submits=True, auto_size_text=True, enable_events=True, expand_x=True, expand_y=True, key=args[1])

		def slider(args):
			return sg.Slider(range=args[0], default_value=args[1], orientation=args[2], expand_x = True, enable_events = True, change_submits = True, key=args[3])

		def radio(args):
			#print (args)
			return sg.Radio(text=args[0], group_id=[1], default=args[2], auto_size_text = True, key=args[3], enable_events=True, change_submits=True)

		def checkbox(args):
			return sg.Checkbox(text=args[0], auto_size_text=True, change_submits=True, enable_events=True, key=args[1])

		def image(args):
			if len(args) == 1:
				key = args[0]
				src = ''
			elif len(args) == 2:
				src = args[0]
				key = args[1]
			return sg.Image(src, subsample=4, expand_x=True, expand_y=True, enable_events=True, key=key)
		
		if args == []:
			print ("Argument dictionary not provided! Aborting...", args)
			return None

		if elem == 'dropdown_menu':
			return dropdown_menu(args)
		elif elem == 'textbox':
			return textbox(args)
		elif elem == 'text_input':
			return text_input(args)
		elif elem == 'btn':
			return btn(args)
		elif elem == 'listbox':
			return listbox(args)
		elif elem == 'slider':
			return slider(args)
		elif elem == 'radio':
			return radio(args)
		elif elem == 'checkbox':
			return checkbox(args)
		elif elem == 'image':
			return image(args)
		else:
			print ("element not found: ", elem)
			return None


	def get_events(self):
		try:
			self.window, self.event, self.values = sg.read_all_windows(timeout=10)
			return (self.window, self.event, self.values)
		except Exception as e:
			print ("Error in get_events, line 153", e)
			return (None, None, None)


	def set_window_screen(self, screen):
		if screen not in list(self.conf['screens'].keys()):
			print ("Screen id not found:", screen)
			return False
		self.conf['screen'] = int(screen)
		self.RESET = True
		self.WINDOW.close()
		#self.WINDOW2.close()

	def set_window_reset(self):
		self.RESET = True


	def clear_window_reset(self):
		self.RESET = False


	def dump_layout(self, layout, filename):
		with open (filename, 'w') as f:
			layout = str(layout)
			f.write(layout)
		f.close()
		with open (filename, 'a') as f:
			f.write('ELEMENT_START')
