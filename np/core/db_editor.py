import np
import PySimpleGUI as sg
import subprocess
global WINDOW, WINDOW2
def sqlite3(com):
	path = (f"{np.DATA_DIR}/nplayer.db")
	com = (f"sqlite3 '{path}' '{com}'")
	print (f"Query: '{com}'")
	ret = subprocess.check_output(com, shell=True).decode().strip()
	return (ret)


def get_series_list():
	com = (f"select distinct series_name from series;")
	_list = sqlite3(com).split('\n')
	return _list

def get_movies_list():
	com = (f"select distinct title from movies;")
	_list = sqlite3(com).split('\n')
	return _list

def get_music_list():
	com = (f"select distinct artist,title from music;")
	_list = sqlite3(com).split('\n')
	return _list

def get_details_movies(title):
	com = (f"select * from movies where title like '%{title}%';")
	_list = sqlite3(com).split('|')
	return _list

def get_seasons(series_name):
	com = (f"select distinct season from series where series_name like \"%{series_name}%\";")
	_list = sqlite3(com).split('\n')
	return _list

def get_episodes(series_name, season):
	com = (f"select distinct episode_number,episode_name from series where series_name like \"%{series_name}%\" and season = {season};")
	_list = sqlite3(com).split('\n')
	return _list


def get_table(values):
	if values['-table_series-'] == True:
		return 'series'
	elif values['-table_music-'] == True:
		return 'music'
	elif values['-table_movies-'] == True:
		return 'movies'

def edit_details(table, _id):
	global h
	ew, eh = WINDOW.CurrentLocation()
	eh = eh + h
	print (f"Coords: ({ew}, {eh})")
	schema = np.get_columns(table)
	columns = list(schema.keys())
	com = (f"select * from {table} where id = {_id};")
	info = sqlite3(com).split('|')
	pos = -1
	layout = []
	for column in columns:
		pos += 1
		try:
			txt = info[pos]
			if '"' in txt:
				chunks = txt.split('"')
				j = ''
				txt = j.join(chunks)
			if "'" in txt:
				chunks = txt.split("'")
				j = ''
				txt = j.join(chunks)
			key = (f"-{column}-")
			txtinput = [sg.Text(key), sg.Input(default_text=txt, enable_events=True, do_not_clear=True, key=key, expand_x=True)]
			layout.append(txtinput)
		except:
			pass
	btns = [[sg.Button('-update-'), sg.Button('-cancel-')]]
	layout.append(btns)
	WINDOW2 = sg.Window('Edit details', layout, location=(ew,eh), size=(640, 400), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
	while True:
		tevent, tvalues = WINDOW2.read(timeout=10)
		if tevent is not None and tevent != '__TIMEOUT__':
			if tevent ==  sg.WIN_CLOSED:
				break
			if tevent == '-cancel-':
				WINDOW2.close()
				break
			else:
				print (tevent, tvalues)
	return True


def set_active_series(isactive = None, series_name=None, season=None, episode_number=None):
	if isactive is None:
		print ("Is active value not provided, setting to 1.")
		isactive = 1
	print (f"Setting Active = {isactive}...")
	if episode_number is not None and season is not None and series_name is not None:
		com = (f"update series set isactive = {isactive} where series_name like \"%{series_name}%\" and season = {season} and episode_number = {episode_number};")
		ret = sqlite3(com)
		return ret
	elif episode_number is None and season is not None and series_name is not None:
		com = (f"select id from series where series_name like \"%{series_name}%\" and season = {season};")
		items = sqlite3(com).split('\n')
		for _id in items:
			com = (f"update series set isactive = {isactive} where id = {_id};")
			ret = sqlite3(com)
		return ret
	elif episode_number is None and season is None and series_name is not None:
		com = (f"select id,isactive from series where series_name like \"%{series_name}%\";")
		items = sqlite3(com).split('\n')
		for _id in items:
			com = (f"update series set isactive = {isactive} where id = {_id};")
			ret = sqlite3(com)
		return ret
	elif episode_number is None and season is None and series_name is None:
		print ("No details given! Applying to entire database...")
		com = ("update series set isactive = {isactive};")
		ret = sqlite3(com)
		return ret


def show_editor():
	global h
	table = 'series'
	db_items_0 = get_series_list()
	db_items_1 = []
	db_items_2 = []
	radio_sql_table_select = [[sg.Radio('series', "TABLES", default=True, enable_events=True, key='-table_series-'), sg.Radio('movies', "TABLES", default=False, enable_events=True, key='-table_movies-'), sg.Radio('music', "TABLES", default=False, enable_events=True, key='-table_music-'), sg.Button(button_text='select_all', auto_size_button=True, pad=(1, 1), expand_x=True, key='-select_all-'), sg.Button(button_text='clear_all', auto_size_button=True, pad=(1, 1), expand_x=True, key='-clear_all-')]]
	listbox_dbitems = [[sg.Listbox(db_items_0, size=(20, 10), select_mode='multiple', change_submits=True, auto_size_text=True, enable_events=True, key='-db_items_0-'), sg.Listbox(db_items_1, size=(10, 10), select_mode='multiple', change_submits=True, auto_size_text=True, expand_x=True, enable_events=True, key='-db_items_1-'), sg.Listbox(db_items_2, size=(20, 10), select_mode='multiple', change_submits=True, auto_size_text=True, enable_events=True, key='-db_items_2-')]]
	line_controls = [[sg.Button(button_text='load', auto_size_button=True, pad=(1, 1), expand_x=True, key='-load_info-'), sg.Button(button_text='quit', auto_size_button=True, pad=(1, 1), expand_x=True, key='-quit-'), sg.Button(button_text='open editor', auto_size_button=True, pad=(1, 1), expand_x=True, key='-open_editor-'), sg.Button(button_text='Set Active', auto_size_button=True, pad=(1, 1), expand_x=True, key='-set_active-'), sg.Button(button_text='Set Inactive', auto_size_button=True, pad=(1, 1), expand_x=True, key='-set_inactive-')]]
	layout = [
		radio_sql_table_select,
		listbox_dbitems,
		line_controls,
		[sg.Sizegrip(key='-gui_size-')],
		[]
	]
	
	
	h = 640
	w = 320
	title = None
	series_name = None
	artist = None
	season = None
	episode_number = None
	episode_name = None
	WINDOW = sg.Window('GUI', layout, location=(0,0), size=(h, w), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
	return WINDOW

			
def run():
	global WINDOW
	WINDOW = show_editor()
	while True:
		window, event, values = sg.read_all_windows(timeout=10)
		try:
			table = get_table(values)
		except:
			table = 'series'
		if event is not None and event != '__TIMEOUT__':
			if event ==  sg.WIN_CLOSED:
				break
			if event == '-quit-':
				WINDOW.close()
				break
			elif event == '-table_movies-' or event == '-table_music-' or event == '-table_series-':
				print (event)
				table = get_table(values)
				if table == 'movies':
					db_items_0 = get_movies_list()
				elif table == 'series':
					db_items_0 = get_series_list()
				elif table == 'music':
					db_items_0 = get_music_list()
				db_items_1 = []
				db_items_2 = []
				WINDOW['-db_items_1-'].update(db_items_1)
				WINDOW['-db_items_2-'].update(db_items_2)
				WINDOW['-db_items_0-'].update(db_items_0)
			elif event == '-db_items_0-':
				try:
					print (event)
					table = get_table(values)
					if table == 'movies':
						items = values[event]
						if len(items) > 1:
							print ("More than one item selected, skipping grab additional info.")
						else:
							title = values[event][0]
							print (f"Title: '{title}'")
					elif table == 'series':
						items = values[event]
						if len(items) > 1:
							print ("More than one item selected, skipping grab additional info.")
						else:
							series_name = items[0]
							db_items_1 = get_seasons(series_name)
							WINDOW['-db_items_1-'].update(db_items_1)
					elif table == 'music':
						items = values[event]
						if len(items) > 1:
							print ("More than one item selected, skipping grab additional info.")
						else:
							artist = items[0].split('|')[0]
							title = items[0].split('|')[1]
							print (f"Artist: '{artist}', Title: '{title}'")
				except Exception as e:
					title = None
					series_name = None
					artist = None
					season = None
					episode_number = None
					episode_name = None
					db_items_1 = []
					db_items_2 = []
					WINDOW['-db_items_1-'].update(db_items_1)
					WINDOW['-db_items_2-'].update(db_items_2)
			elif event == '-db_items_1-':
				print (event)
				try:
					if series_name is None:
						series_name = values['-db_items_0-'][0]
					season = values['-db_items_1-'][0]
					print (f"Series name: {series_name}, season={season}")
					db_items_2 = get_episodes(series_name, season)
					WINDOW['-db_items_2-'].update(db_items_2)
				except Exception as e:
					season = None
					episode_number = None
					episode_name = None
					db_items_2 = []
					WINDOW['-db_items_2-'].update(db_items_2)
			elif event == '-db_items_2-':
				print (event)
				try:
					if series_name is None:
						series_name = values['-db_items_0-'][0]
					if season is None:
						season = values['-db_items_1-'][0]
					episode_number = values['-db_items_2-'][0].split('|')[0]
					print (f"Series name: {series_name}, season={season}, episode_number={episode_number}")
					episode_name = values['-db_items_2-'][0].split('|')[1]
				except Exception as e:
					episode_name = None
					episode_number = None
			elif event == '-open_editor-':
				if table == 'series':
					if series_name is not None and season is not None and episode_number is not None:	
						com = (f"select id from series where series_name like \"%{series_name}%\" and season = {season} and episode_number = {episode_number};")
						_id = sqlite3(com)
						print (f"ID: {_id}")
						edit_details(table, _id)
					else:
						print (f"Please set all fields first: series_name='{series_name}', season={season}, episode_number={episode_number}")
				elif table == 'music':
					artist = values['-db_items_0-'][0].split('|')[0]
					title = values['-db_items_0-'][0].split('|')[1]
					com = (f"select id from music where artist like \"%{artist}%\" and title = \"{title}\";")
					_id = sqlite3(com)[0]
					print (f"ID: {_id}")
					edit_details(table, _id)
				elif table == 'movies':
					title = values['-db_items_0-'][0]
					com = (f"select id from movies where title like \"%{title}%\";")
					_id = sqlite3(com)[0]
					print (f"ID: {_id}")
					edit_details(table, _id)
			elif event == '-set_active-':
				print (f"Setting active: Table='{table}', Series: '{series_name}', Season: {season}, Episode Number: {episode_number}")
				if table == 'series':
					if series_name is not None and season is not None and episode_number is not None:
						ret = set_active_series(isactive=1, series_name=series_name, season=season, episode_number=episode_number)
						print (ret)
					elif series_name is not None and season is not None and episode_number is None:
						ret = set_active_series(isactive=1, series_name=series_name, season=season)
						print (ret)
					elif series_name is not None and season is None and episode_number is None:
						ret = set_active_series(isactive=1, series_name=series_name)
						print (ret)
					else:
						print ("No series selected!")
				if table == 'movies':
					if title is not None:
						com = f("update movies set isactive = 1 where title like \"%{title}%\";")
						ret = sqlite3(com)
						print (ret)
					else:
						print ("No title set!")
				if table == 'music':
					if title is not None and artist is not None:
						com = f("update music set isactive = 1 where title like \"%{title}%\" and artist like \"{artist}\";")
						ret = sqlite3(com)
						print (ret)
					elif title is None and artist is not None:
						com = f("update music set isactive = 1 where artist like \"{artist}\";")
						ret = sqlite3(com)
						print (ret)
					elif title is not None and artist is None:
						com = f("update music set isactive = 1 where title like \"{title}\";")
						ret = sqlite3(com)
						print (ret)
					else:
						print ("No title set!")
			elif event == '-set_inactive-':
				print (f"Setting Inactive: Table='{table}', Series: '{series_name}', Season: {season}, Episode Number: {episode_number}")
				if table == 'series':
					if series_name is not None and season is not None and episode_number is not None:
						ret = set_active_series(isactive=0, series_name=series_name, season=season, episode_number=episode_number)
						print (ret)
					elif series_name is not None and season is not None and episode_number is None:
						ret = set_active_series(isactive=0, series_name=series_name, season=season)
						print (ret)
					elif series_name is not None and season is None and episode_number is None:
						ret = set_active_series(isactive=0, series_name=series_name)
						print (ret)
					else:
						print ("No series selected!")
				if table == 'movies':
					if title is not None:
						com = f("update movies set isactive = 0 where title like \"%{title}%\";")
						ret = sqlite3(com)
						print (ret)
					else:
						print ("No title set!")
				if table == 'music':
					if title is not None and artist is not None:
						com = f("update music set isactive = 0 where title like \"%{title}%\" and artist like \"{artist}\";")
						ret = sqlite3(com)
						print (ret)
					elif title is None and artist is not None:
						com = f("update music set isactive = 0 where artist like \"{artist}\";")
						ret = sqlite3(com)
						print (ret)
					elif title is not None and artist is None:
						com = f("update music set isactive = 0 where title like \"{title}\";")
						ret = sqlite3(com)
						print (ret)
					else:
						print ("No title set!")
			elif event == '-clear_all-':
				db_items_0 = []
				db_items_1 = []
				db_items_2 = []
				WINDOW['-db_items_0-'].update(db_items_0)
				WINDOW['-db_items_1-'].update(db_items_1)
				WINDOW['-db_items_2-'].update(db_items_2)
				title = None
				series_name = None
				artist = None
				season = None
				episode_number = None
				episode_name = None
			else:
				print (window, event, values)
