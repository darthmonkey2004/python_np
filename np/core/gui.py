from np import xrandr
import sys, traceback
import subprocess
import os
from np import log as logger
import np
import PySimpleGUI as sg
from np.core.conf import readConf
home = os.path.expanduser("~")
DATA_DIR = (home + os.path.sep + ".np")
conf = np.readConf()
#-----------main gui creation class------------#


def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)


def file_browse_window(cwd=None):
	if cwd == None:
		cwd = DATA_DIR
	x = conf['windows']['browser']['x']
	y = conf['windows']['browser']['y']
	w = conf['windows']['browser']['w']
	h = conf['windows']['browser']['h']
	filepath = None
	file_browser_layout = [[sg.T("")], [sg.Text("Choose a file: "), sg.Input(cwd, key='-path-', enable_events=True), sg.FileBrowse(initial_folder=cwd, key="-IN-")],[sg.Button("Submit")]]
	file_browser_window = sg.Window('Load Media file or playlist...', file_browser_layout, location=(int(x), int(y)), size=(int(w), int(h)))
	while True:
		file_browser_event, file_browser_values = file_browser_window.read()
		if file_browser_event == sg.WIN_CLOSED or file_browser_event=="Exit":
			filepath = None
			break
		elif file_browser_event == "Submit":
			try:
				filepath = file_browser_values["-IN-"]
				file_browser_window.close()
				break
			except:
				filepath = file_browser_values['-path-']
				file_browser_window.close()
				break
			
	return filepath




def folder_browse_window(cwd=None):
	if cwd == None:
		cwd = DATA_DIR
	x = conf['windows']['browser']['x']
	y = conf['windows']['browser']['y']
	w = conf['windows']['browser']['w']
	h = conf['windows']['browser']['h']
	path = None
	folder_browser_layout = [[sg.T("")], [sg.Text("Choose directory: "), sg.Input(cwd, key='-path-', enable_events=True), sg.FolderBrowse(initial_folder=cwd, key="-SAVE_PATH-")], [sg.Button("Submit")]]
	folder_browser_window = sg.Window("Save playlist file...", folder_browser_layout, location=(int(x), int(y)), size=(int(w), int(h)))
	while True:
		folder_browser_event, folder_browser_values = folder_browser_window.read(timeout=1)
		if folder_browser_event == '__TIMEOUT__':
			pass
		if folder_browser_event == sg.WIN_CLOSED or folder_browser_event=="Exit":
			path = None
			return None
		elif folder_browser_event == "Submit":
			try:
				path = folder_browser_values["-SAVE_PATH-"]
				folder_browser_window.close()
				if path == '':
					path = cwd
				break
			except:
				path = folder_browser_values['-path-']
				folder_browser_window.close()
				if path == '':
					path = cwd
				break
	return path


def db_editor():
	com = (f"python3 -c \"import np; np.db_editor()\"&")
	subprocess.call(com, shell=True)
	return True

def tag_editor():
	com = (f"python3 -c \"import np; np.tag_editor()\"&")
	subprocess.call(com, shell=True)
	return True

def bring_to_front(win):
	win.bring_to_front()
	log(f"Window ({win.Title}) on the front lines!", 'info')
	return True

def send_to_back(win):
	win.send_to_back()
	log(f"Window ({win.Title}) in the rear with the gear!", 'info')
	return True


def run_long_operation(func, end_key):
	return perform_long_operation(func, end_key)


def write_event(event, value, win):
	return win.write_event_value(event, value)


def restore(win):
	win.normal()
	log(f"Window ({win.Title}) restored!", 'info')


def maximize(win):
	win.maximize()
	log(f"Window ({win.Title}) maximized!", 'info')


def hide(win):
	win.hide()
	log(f"Window ({win.Title}) hidden!", 'info')


def un_hide(win):
	win.un_hide()
	log(f"Window ({win.Title}) un-hidden!", 'info')


def reappear(win):
	win.reappear()
	log(f"Window ({win.Title}) revealed!", 'info')


def dissapear(win):
	win.dissapear()
	log(f"Window ({win.Title}) dissapeared!", 'info')


def get_pointer(win):
	return win.mouse_location()


def minimize(win):
	win.minimize()
	log(f"Window ({win.Title}) minimized!", 'info')


def start_thread(function, key, win):
	try:
		ret = win.start_thread(function, key)
		if ret is not None:
			log(f"Thread start returned data: {ret}", 'info')
		return True
	except Exception as e:
		log(f"Exception in start_thread: {e}", 'error')
		return False


def get_scaling():
    # called before window created
    root = sg.tk.Tk()
    scaling = root.winfo_fpixels('1i')/72
    root.destroy()
    return scaling


class gui():
	def __init__(self):
		self.TAB = '-player_control_layout-'
		self.RESET = False
		self.win_type = 'internal'
		self.player = np.nplayer()
		self.playlist = self.player.create_media()
		self.conf = np.readConf()
		self.windows = []
		self.conf['active_windows'] = self.windows
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
		try:
			state = self.conf['windows']['visible_state']
		except:
			self.conf['windows'] = np.init_window_position()
			state = self.conf['windows']['gui']['visible_status']
		viewer_screen = self.conf['screen']
		if viewer_screen == 0:
			screen = 1
		elif viewer_screen == 1:
			screen = 0
		else:
			screen = 0
		self.gui_win_x = self.conf['windows']['gui'][state][screen]['x']
		self.gui_win_y = self.conf['windows']['gui'][state][screen]['y']
		self.gui_win_w = self.conf['windows']['gui'][state][screen]['w']
		self.gui_win_h = self.conf['windows']['gui'][state][screen]['h']
		log(f"GUI window set: {self.gui_win_x}, {self.gui_win_y}, {self.gui_win_w}, {self.gui_win_y}", 'info')
		self.viewer_win_x = self.conf['windows']['viewer'][viewer_screen]['x']
		self.viewer_win_y = self.conf['windows']['viewer'][viewer_screen]['y']
		self.viewer_win_w = self.conf['windows']['viewer'][viewer_screen]['w']
		self.viewer_win_h = self.conf['windows']['viewer'][viewer_screen]['h']
		log(f"Viewer window set: {self.viewer_win_x}, {self.viewer_win_y}, {self.viewer_win_w}, {self.viewer_win_h}", 'info')
		#self.window = None
		self.event = None
		self.values = None
		self.player_window_layout = []
		self.uievent = None
		self.uivalues = {}
		#self.window = None
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
		title = self.WINDOW2.Title
		if title not in self.windows:
			self.windows.append(title)
			log(f"Added {title} to self.windows! ({self.windows})", 'info')
		else:
			log(f"Warning: {title} already in self.windows! ({self.windows})", 'warning')
		self.RESET = False
		self.icon_path = f"{np.HOME}/.local/poster.png"
		sg.set_global_icon(self.icon_path)


	def list_active_windows(self):
		return self.windows


	def create_gui_window(self):
		line = []
		log_data = 'Nyuh-uh!'
		scale = float(int(self.conf['scale']) * 10)
		control_modes = self.conf['network_modes']['control_modes']
		media_modes = self.conf['network_modes']['media_modes']
		search_line = [self.create_old('dropdown_menu', [self.tables, self.conf['play_type'], '-PLAY_TYPE-']), self.create_old('dropdown_menu', [list(self.conf['screens'].keys()), self.conf['screen'], '-SET_SCREEN-']), self.create_old('dropdown_menu', [['database', 'playlist'], 'database', '-PLAY_MODE-']), self.create_old('dropdown_menu', [control_modes, self.conf['network_mode']['control_mode'], '-CONTROL_MODE-']), self.create_old('dropdown_menu', [media_modes, self.conf['network_mode']['media_mode'], '-MEDIA_MODE-']), self.create_old('textbox', ['Search', '-SEARCH-']), self.create_old('text_input', ['Enter search query:', '-SEARCH_QUERY-']), self.create_old('btn', ['Search', 'Search'])]
		debug_element = sg.Multiline(default_text=log_data, enter_submits=True, autoscroll=True, auto_size_text=True, horizontal_scroll=True, change_submits=True, enable_events=True, key='-DEBUGGER-', auto_refresh=True, reroute_stdout=False, reroute_stderr=False, reroute_cprint=False, echo_stdout_stderr=False, focus=False, expand_x=True, expand_y=True, rstrip=True)
		elem_media_list = [self.create_old('listbox', [self.playlist, '-CURRENT_PLAYLIST-']), debug_element]
		update_line = [self.create_old('btn', ['Refresh from Database']), self.create_old('btn', ['Refresh Log Data'])]
		player_controls1 = [self.create_old('btn', ['Volume Up']), self.create_old('btn', ['previous']), self.create_old('btn', ['play']), self.create_old('btn', ['next']), self.create_old('btn', ['pause']), self.create_old('btn', ['stop'])]
		player_controls2 = [self.create_old('btn', ['Volume Down']), self.create_old('btn', ['seek fwd']), self.create_old('btn', ['seek rev']), self.create_old('btn', ['Exit']), self.create_old('btn', ['Screenshot']), self.create_old('btn', ['Mark Intro: Start']), self.create_old('btn', ['Mark Intro: End'])]
		try:
			play_pos = float(self.conf['nowplaying']['play_pos'])
		except:
			play_pos = 0
			self.conf['nowplaying']['play_pos'] = play_pos
		slider_scale = [sg.Slider(range=(0,1), resolution=0.01, default_value=play_pos, orientation='h', expand_x = True, enable_events = True, change_submits = True, key='-PLAY_POS-')]
		line_window_ctl = [self.create_old('btn', ['store window location']), self.create_old('btn', ['Recenter UI']), self.create_old('btn', ['Fix Focus']), self.create_old('btn', ['Fix Scaling'])]
		self.video_temp_img = self.create_old('image', [np.DEFAULT_POSTER, '-VID_OUT-'])
		
		line.append(self.video_temp_img)
		
		self.player_window_layout.append(line)
		self.player_window_layout.append([sg.Sizegrip(key='-viewer_size-')])
		table = self.play_type
		columns_list = list(np.get_columns(table).keys())
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
			[sg.Sizegrip(key='-gui_size-')],
			[]
		]
		dbitems = []
		self.menu_def = [['&File', ['-&Load Directory-', '-&Load Playlist-', '-&Save Playlist-', 'E&xit']], ['&Tools', ['&Pirate Bay Downloader', '-&Database Editor-', '-ID3 Tag Editor-', '&Torrent Manager', '&Video Filters', [np.VLC_VIDEO_FILTERS], '&Audio Filters', [np.VLC_AUDIO_FILTERS]]], ['&Help', '&About...'], ['&Media', ['-Scan Movies-', '-Scan Series-', '-Scan Music-', '-Scan All-', '-Clean Database-']]]
		#self.layout = [[sg.MenubarCustom(self.menu_def, tearoff=True, key='-menubar_key-'), sg.Button("Close")], [sg.TabGroup([[sg.Tab('MP Controls', self.player_control_layout, key='-player_control_layout-')], [sg.Tab('DB Manager', self.db_mgr_layout, key='-db_mgr_layout-')]], 	expand_x=True, expand_y=True, enable_events=True)]]
		self.layout = [[sg.MenubarCustom(self.menu_def, tearoff=True, key='-menubar_key-'), sg.Button('Hide UI'), sg.Button("Close")], [sg.TabGroup([[sg.Tab('MP Controls', self.player_control_layout, key='-player_control_layout-')], line_window_ctl], expand_x=True, expand_y=True, enable_events=True)]]
		if 'GUI' not in self.windows:
			self.windows.append('GUI')
			log(f"Added 'GUI' to self.windows ({self.windows})", 'info')
		else:
			log(f"Warning: 'GUI' already in self.windows! Not creating...({self.windows})", 'warning')
			try:
				raise Exception("Window already created!")
				log("Window already created!", 'error')
			except:
				log("Window already created!", 'error')
		win = sg.Window('GUI', self.layout, no_titlebar=True, location=(int(self.gui_win_x),int(self.gui_win_y)), size=(self.gui_win_w,self.gui_win_h), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True)
		self.viewer_win_w, self.viewer_win_h = xrandr()[conf['screen']]['w'], xrandr()[conf['screen']]['h']
		self.viewer_win_scale = get_scaling()
		return win




	def init_window_position(self):
		screen = self.conf['screen']
		self.conf['windows'] = np.init_window_position()
		np.writeConf(self.conf)
		return self.conf['windows']

	def fix_focus(self):
		try:
			self.WINDOW.TKroot.focus_force()
			self.WINDOW.Element('-SEARCH_QUERY-').SetFocus()
			log(f"Fixed focus!", 'info')
		except Exception as e:
			log(f"Unable to set focus: {e}. Is GUI window open?", 'error')


	def get_window_location(self, window=None):
		if window == None:
			log(f"Error Getting Window location: Name=None, no name provided. Options are 'viewer/player', and 'gui'.", 'error')
			return False
		elif window == 'player' or window == 'viewer':
			try:
				coords = self.WINDOW2.CurrentLocation()
			except Exception as e:
				log(f"Error Getting Window location: Name={window} appears to be closed!", 'error')
				return None
		elif window == 'gui':
			try:
				coords = self.WINDOW.CurrentLocation()
			except Exception as e:
				log(f"Error Getting Window location: Name=appears to be closed!", 'error')
				return None
		log(f"Window location: Name={window}, Coords={coords}", 'info')
		return coords

	def db_editor(self):
		db_editor()
		
	def tag_editor(self):
		tag_editor()


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
		log(f"{window} window moved to!", 'info')
			
			
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


	def get_user_yn(self, window_title='Yes/No'):
		yes_btn = sg.Button(button_text='Yes', auto_size_button=True, pad=(1, 1), key='-YES-')
		no_btn = sg.Button(button_text='No', auto_size_button=True, pad=(1, 1), key='-NO-')
		layout = [[yes_btn], [no_btn]]
		input_window = sg.Window(window_title, layout, size=(300, 100), keep_on_top=False, element_justification='center', finalize=True)
		while True:
			event, values = input_window.read()
			if event == sg.WIN_CLOSED:
				break
			elif event == '-YES-':
				user_input = True
				input_window.close()
			elif event == '-NO-':
				user_input = False
			self.user_input = user_input
			break
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


	def toggle_on_top(self, win):
		state = win.KeepOnTop
		if state:
			ret = False
			win.keep_on_top_clear()
			log(f"Window '{win.Title}': keep_on_top cleared!", 'info')
		else:
			ret = True
			win.keep_on_top_set()
			log(f"Window '{win.Title}': keep_on_top set!", 'info')
		return ret


	def set_window_screen(self, screen: int, conf=None):
		if conf == None:
			self.conf = np.readConf()
		else:
			self.conf = conf
		self.conf['screen'] = screen
		try:
			state = self.conf['windows']['gui']['visible_status']
		except:
			self.conf['windows'] = np.init_window_position()
			state = self.conf['windows']['gui']['visible_status']
		if screen == 1:
			gui_screen = 0
		elif screen == 0:
			gui_screen = 1
		dims = self.conf['screens'][screen]
		gui_dims = self.conf['screens'][gui_screen]
		w, h, x, y = dims['w'], dims['h'], dims['pos_x'], dims['pos_y']
		self.conf['windows']['viewer']['w'] = w
		self.conf['windows']['viewer']['h'] = h
		self.conf['windows']['viewer']['x'] = x
		self.conf['windows']['viewer']['y'] = y
		self.conf['windows']['gui'][state][gui_screen]['w'] = 1024
		self.conf['windows']['gui'][state][gui_screen]['h'] = 600
		x, y = gui_dims['pos_x'], gui_dims['pos_y']
		self.conf['windows']['gui'][state][gui_screen]['x'] = x
		self.conf['windows']['gui'][state][gui_screen]['y'] = y
		return self.conf

	def dump_object(self, _object, filename):
		with open (filename, 'w') as f:
			ret = obj_to_string(_object)
			f.write(ret)
		f.close()
		return filename
