import pickle
import PySimpleGUI as sg
import subprocess
import os
from np import readConf, get_columns, log, SFTP_DIR
from np.utils.pbdl_se_isin import se_isin, parse
from np.utils.query_series import tmdb_query_series
from np.utils.rotten_tomatoes_query import get_episode_data
conf = readConf()
play_type = conf['play_type']

def save_torrent_log(torrents):
	log(f"Saving current data!", 'info')
	try:
		with open("torrents.log", "wb") as f:
			pickle.dump(torrents, f)
		f.close()
		if conf['debug'] == True:
			log(f"Torrent log updated: {torrents.keys()}", 'info')
		return True
	except Exception as e:
		log(f"Error: Unable to write torrent log {e}: data: {torrents}", 'error')
		return False


def update_media_type(play_type=None):
	diff = 0
	extra_length = 0
	play_type = play_type
	columns_list = list(get_columns(play_type))
	columns_ct = len(columns_list)
	old_columns_ct = columns_ct
	log(f"Type changed:{play_type}", 'info')
	columns_list = list(get_columns(play_type).keys())
	columns_ct = len(columns_list)
	if columns_ct <= 13:
		extra_length = 13 - columns_ct - 1
		if extra_length >= 0:
			columns_ct = extra_length + columns_ct
		elif extra_length < 0:
			columns_ct = extra_length - columns_ct
		print ("Extra Length:", extra_length)
	pos = -1
	
	if len(columns_list) < columns_ct:
		d = 13 - len(columns_list) - 1
		for i in (0, d):
			string = (f"No Field{i}")
			columns_list.append(string)
	for i in range(0, columns_ct):
		column = columns_list[i]
		pos = str(int(pos) + 1)
		d = ("d_" + pos)
		try:
			pbdl_win[d].update(column)
			if diff >= 0:
				for i in range(columns_ct, extra_length):
					d = ("d_" + str(i))
					pbdl_win[d].update('None')
		except:
			break
	pbdl_win.refresh()

	
def select_torrent(tid=None):

	play_type = 'series'
	torrents[tid]['play_type'] = play_type
	pragma = get_columns(play_type)
	columns = list(pragma.keys())
	print ("Columns:", columns, "Play type:", play_type)
	for column in columns:
		field = (f"-{columns.index(column)}-")
		if column == 'id':
			pbdl_win[field].update(tid)
		elif column == 'filepath':
			
			idx = columns.index('filepath')
			k = (f"-{idx}-")
			try:
				filepath = values[k]
			except:
				filepath = torrents[tid]['files'][0]
		else:
			try:
				pbdl_win[field].update(torrents[tid][column])
			except:
				torrents[tid][column] = 'Unknown'
				pbdl_win[field].update(torrents[tid][column])
				
	play_type = torrents[tid]['play_type']
	pbdl_win['-MEDIA_TYPE-'].update(play_type)
	update_media_type(play_type)
	files = torrents[tid]['files']
	name = torrents[tid]['name']
	pbdl_win['-tid-'].update(tid)
	pbdl_win['-Name-'].update(name)
	string = (str(torrents[tid]['have']) + " " + str(torrents[tid]['size_unit']))
	pbdl_win['-Have-'].update(string)
	pbdl_win['-ETA-'].update(torrents[tid]['eta'])
	pbdl_win['-Upload Rate-'].update(torrents[tid]['up'])
	pbdl_win['-Download Rate-'].update(torrents[tid]['down'])
	pbdl_win['-Status-'].update(torrents[tid]['status'])
	pbdl_win['-Ratio-'].update(torrents[tid]['ratio'])
	print (torrents.keys())
	pbdl_win['-TORRENT_FILES-'].update(files)
	pbdl_win['-Percent-'].update(torrents[tid]['percent'])
	return torrents[tid]



def load_saved_data():
	bakdata = {}
	log("Restoring backup...")
	if os.path.exists("torrents.log"):
		with open("torrents.log", "rb") as f:
			bakdata = pickle.load(f)
		f.close()
	log("Backup restored!", 'info')
	return bakdata


def display_torrents(data=None):
	active_torrents = []
	if data == None:
		torrents = build_torrents()
	else:
		torrents = data
	for tid in list(torrents.keys()):
		try:
			play_type = torrents[tid]['play_type']
			play_type = 'series'
			name = torrents[tid]['name']
			percent = torrents[tid]['percent']
			string = (f"{tid}:{play_type}:{percent}:{name}")
			active_torrents.append(string)
		except Exception as e:
			print (f"Exception, display_torrents(), {e}")
			#torrents[tid]['play_type'] = 'Unknown Type'
			percent = torrents[tid]['percent']
			name = torrents[tid]['name']
			string = (f"{tid}:{percent}:{name}")
			active_torrents.append(string)
	print (active_torrents)
	return active_torrents


def create_torrent_mgr():
	active_torrents = []
	
	global conf
	
	menu_def = [['&File', ['E&xit']], ['&Toolbar', ['&Rotten Tomatoes Query', '&Remove Torrent', '&Delete Torrent', '&Query TMDB', 'VPN', ['&0 Off', '&1 On', '&2 Status'], 'View &Downloader']], ['&Help', '&About...']]
	columns_list = list(get_columns(play_type).keys())
	pbdl_layout = [
	[sg.Listbox(active_torrents, expand_x=True, enable_events=True, size=(50,10), key='-TORRENT_SELECT-')],
	[sg.Text('tid:'), sg.Text('', expand_x=True, key='-tid-')],
	[sg.Text('Name:'), sg.Text('', expand_x=True, key='-Name-')],
	[sg.Text('Percent:'), sg.Text('', expand_x=True, key='-Percent-')],
	[sg.Text('Have:'), sg.Text('', expand_x=True, key='-Have-')],
	[sg.Text('ETA:'), sg.Text('', expand_x=True, key='-ETA-')],
	[sg.Text('Upload Rate:'), sg.Text('', expand_x=True, key='-Upload Rate-')],
	[sg.Text('Download Rate:'), sg.Text('', expand_x=True, key='-Download Rate-')],
	[sg.Text('Status:'), sg.Text('', expand_x=True, key='-Status-')],
	[sg.Text('Ratio:'), sg.Text('', expand_x=True, key='-Ratio-')],
	[sg.Listbox([], expand_x=True, expand_y=True, enable_events=True, select_mode='multiple', size=(50,50), key='-TORRENTS-')]

	]
	title_bar_layout = [sg.MenubarCustom(menu_def, tearoff=False, key='-menubar_key-'), sg.Combo(['series', 'movies', 'music'], conf['play_type'] , enable_events=True,key='-MEDIA_TYPE-'), sg.Button("Quit!", key='-Close PBDL-')],
	title_bar_frame = sg.Frame(title='', layout = title_bar_layout, key='title_bar_frame', expand_x=True, grab=True, element_justification="center", vertical_alignment="top")
	media_info_layout = build_column_table(play_type)
	media_info_layout.append([sg.Listbox([], size=(10,10), expand_x=True, expand_y=False, enable_events=True, select_mode='single', key='-TORRENT_FILES-')])
	media_info_actions = [sg.Button('Query TMDB', key='-Query TMDB-'), sg.Button('Migrate Files', key='-Migrate Files-'), sg.Button('Read from database', '-Read from database-'), sg.Button('Remove'), sg.Button('Remove+Delete'), sg.Button('Exclude')]
	media_info_layout.append(media_info_actions)
	info_frame = sg.Frame(title='Torrent Data', layout=pbdl_layout, key='info_frame', expand_x=True, grab=True, element_justification="left", vertical_alignment="top")
	media_info_frame = sg.Frame(title='Media Info', layout=media_info_layout, key='media_info_frame', expand_x=True, grab=True, element_justification="right", vertical_alignment="top")
	layout = [[title_bar_frame], [info_frame, [media_info_frame, sg.Sizegrip(key='-gui_size-')]]]
	try:
		x = int(conf['windows']['pbdl']['x'])
		y = int(conf['windows']['pbdl']['y'])
		w = int(conf['windows']['pbdl']['w'])
		h = (int(conf['windows']['pbdl']['h']) + 100)
	except:
		conf = readConf()
		screen = conf['screen']
		x, y = conf['screens'][screen]['pos_x'], conf['screens'][screen]['pos_y']
		w = conf['windows']['pbdl_dl']['w']
		h = conf['windows']['pbdl_dl']['h']
	pbdl_win = sg.Window('GUI', layout, no_titlebar=False, location=(x,y), size=(600,900), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
	return pbdl_win



def build_column_table(play_type=None):
	media_info_layout = []
	is_active_ckbox = [sg.Button('Refresh From Remote', key='-REFRESH_DATA-'), sg.Button('Load Info', key='-LOAD_INFO-'), sg.Button('Save Info', key='-SAVE_INFO-'), sg.Checkbox(text='Is Active:', auto_size_text=True, change_submits=True, enable_events=True, key='-SET_ACTIVE-'), sg.Checkbox(text='Auto Remove Torrents:', auto_size_text=True, change_submits=True, enable_events=True, key='-AUTO_REMOVE-')]
	media_info_layout.append(is_active_ckbox)
	pos = -1
	columns = list(get_columns(play_type).keys())
	if play_type == 'series':
		media_info_layout.append([sg.Text('id', key='d_0'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-0-", expand_x=True)])
		media_info_layout.append([sg.Text('idactive', key='d_1'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-1-", expand_x=True)])
		media_info_layout.append([sg.Text('series_name', key='d_2'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-2-", expand_x=True)])
		media_info_layout.append([sg.Text('tmdbid', key='d_3'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-3-", expand_x=True)])
		media_info_layout.append([sg.Text('season', key='d_4'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-4-", expand_x=True)])
		media_info_layout.append([sg.Text('episode_number', key='d_5'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-5-", expand_x=True)])
		media_info_layout.append([sg.Text('episode_name', key='d_6'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-6-", expand_x=True)])
		media_info_layout.append([sg.Text('description', key='d_7'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-7-", expand_x=True)])
		media_info_layout.append([sg.Text('air_date', key='d_8'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-8-", expand_x=True)])
		media_info_layout.append([sg.Text('still_path', key='d_9'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-9-", expand_x=True)])
		media_info_layout.append([sg.Text('duration', key='d_10'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-10-", expand_x=True)])
		media_info_layout.append([sg.Text('filepath', key='d_11'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-11-", expand_x=True)])
		media_info_layout.append([sg.Text('md5', key='d_12'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-12-", expand_x=True)])
		media_info_layout.append([sg.Text('url', key='d_13'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-13-", expand_x=True)])
	elif play_type == 'music':
		media_info_layout.append([sg.Text('id', key='d_0'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-0-", expand_x=True)])
		media_info_layout.append([sg.Text('idactive', key='d_1'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-1-", expand_x=True)])
		media_info_layout.append([sg.Text('title', key='d_2'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-2-", expand_x=True)])
		media_info_layout.append([sg.Text('mdbid', key='d_3'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-3-", expand_x=True)])
		media_info_layout.append([sg.Text('album', key='d_4'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-4-", expand_x=True)])
		media_info_layout.append([sg.Text('album_id', key='d_5'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-5-", expand_x=True)])
		media_info_layout.append([sg.Text('artist_id', key='d_6'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-6-", expand_x=True)])
		media_info_layout.append([sg.Text('artist', key='d_7'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-7-", expand_x=True)])
		media_info_layout.append([sg.Text('genre', key='d_8'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-8-", expand_x=True)])
		media_info_layout.append([sg.Text('track', key='d_9'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-9-", expand_x=True)])
		media_info_layout.append([sg.Text('filepath', key='d_10'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-10-", expand_x=True)])
		media_info_layout.append([sg.Text('No Field1', key='d_11'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-11-", expand_x=True)])
		media_info_layout.append([sg.Text('No Field2', key='d_12'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-12-", expand_x=True)])
		media_info_layout.append([sg.Text('No Field3', key='d_13'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-13-", expand_x=True)])

	elif play_type == 'movies':
		media_info_layout.append([sg.Text('id', key='d_0'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-0-", expand_x=True)])
		media_info_layout.append([sg.Text('idactive', key='d_1'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-1-", expand_x=True)])
		media_info_layout.append([sg.Text('tmdbid', key='d_2'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-2-", expand_x=True)])
		media_info_layout.append([sg.Text('title', key='d_3'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-3-", expand_x=True)])
		media_info_layout.append([sg.Text('year', key='d_4'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-4-", expand_x=True)])
		media_info_layout.append([sg.Text('release_date', key='d_5'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-5-", expand_x=True)])
		media_info_layout.append([sg.Text('duration', key='d_6'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-6-", expand_x=True)])
		media_info_layout.append([sg.Text('description', key='d_7'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-7-", expand_x=True)])
		media_info_layout.append([sg.Text('poster', key='d_8'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-8-", expand_x=True)])
		media_info_layout.append([sg.Text('filepath', key='d_9'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-9-", expand_x=True)])
		media_info_layout.append([sg.Text('md5', key='d_10'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-10-", expand_x=True)])
		media_info_layout.append([sg.Text('url', key='d_11'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-11-", expand_x=True)])
		media_info_layout.append([sg.Text('No Field1', key='d_12'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-12-", expand_x=True)])
		media_info_layout.append([sg.Text('No Field2', key='d_13'), sg.Input(default_text='', enable_events=True, do_not_clear=True, key="-13-", expand_x=True)])
	return media_info_layout


def parse_further():
	try:
		play_type == torrents[tid]['play_type']
	except:
		play_type = 'series'
	pragma = get_columns(play_type)
	columns = list(pragma.keys())
	if play_type == 'movies':
		print(event, values['-3-'], play_type)
		columns = list(get_columns('movies').keys())	
		idx = columns.index('title')
		k = (f"-{idx}-")
		title = values[k]
		print ("Title:", title)
		info = get_movie_data(title)
		for key in list(info.keys()):
			if key != 'id':
				val = info[key]
				dtype = pragma[key]['data_type']
				if dtype == 'BOOL' or dtype == 'INTEGER':
					torrents[tid][key] = val
				elif dtype == 'TEXT':
					torrents[tid][key] = f("\'{val}\'")
	elif play_type == 'series':
		pragma = get_columns(play_type)
		columns = list(pragma.keys())
		idx = columns.index('series_name')
		k = (f"-{idx}-")
		series_name = values[k]
		idx = columns.index('seasom')
		k = (f"-{idx}-")
		seasom = values[k]
		idx = columns.index('episode_number')
		k = (f"-{idx}-")
		episode_number = values[k]
		info = get_episode_data(series_name, season, episode_number)
		for key in list(info.keys()):
			if key != 'id':
				val = info[key]
				dtype = pragma[key]['data_type']
				if dtype == 'BOOL' or dtype == 'INTEGER':
					torrents[tid][key] = val
				elif dtype == 'TEXT':
					torrents[tid][key] = f("\'{val}\'")


def get_files(tid):
	com = (f"transmission-remote {conf['pbdl_url']} -t{tid} -f | grep -v \".jpg\" | grep -v \"sample\" | grep -v \"Done\" | grep -v \".srt\" | grep -v \".nfo\" | grep -v \"files)\" | grep -v \".txt\" | cut -d \"/\" -f 2")
	data = send_command(com)
	files = []
	for item in data:
		if item != '':
			item = item.strip()
			files.append(item)
	try:
		pbdl_win['-TORRENTS-'].update(files)
	except:
		pass
	return files


def get_torrents():
	torrents = {}
	com = (f"transmission-remote {conf['pbdl_url']} -l")
	print (com)
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
				tid = chunks[0]
				if '*' in tid:
					tid = int(tid.split('*')[0])
				else:
					tid = int(tid)
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
				#if string not in active_torrents:
				#	active_torrents.append(string)
				torrents[tid] = data
	#try:
		#pbdl_win['-TORRENT_SELECT-'].update(active_torrents)
	#except:
	#	pass
	torrents = torrents
	return torrents


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





if __name__ == "__main__":
	import sys
	try:
		arg1 = sys.argv[1]
	except:
		arg1 = None
	try:
		arg2 = sys.argv[2]
	except:
		arg2 = None
	if arg1 is not None and arg2 is not None:
		func = arg1
		arg2 = arg2
	elif arg2 is None and arg1 is not None:
		func = arg1
		arg = None
	elif arg1 is None and arg2 is None:
		func = None
		arg = None

	if func is not None and arg is not None:
		run_func(arg)
	elif func is not None and arg is None:
		run_func()
	elif func is None and arg is None:
		torrents = get_torrents()
		i = -1
		for tid in torrents.keys():
			files = get_files(tid)
			for f in files:
				i += 1
				torrents[tid][i] = f
			torrents[tid]['isactive'] = 1
			torrents[tid]['files'] = {}
			torrents[tid]['files']['play_type'] = conf['play_type']
			for filepath in torrents[tid]['files']:
				torrents[tid]['files'] = {}
				fname = os.path.basename(filepath)
				l = len(fname) - 4
				fname = fname[:l]
				ext = fname[l:]
				torrents[tid]['ext'] = ext
				test = se_isin(fname)
				if test == True:
					torrents[tid]['files']['filepath']['play_type'] = 'series'
					temp = fname.replace(' ', '.').split(' ')
					for chunk in temp:
						if 'S' in chunk and 'E' in chunk:
							season = chunk.split('S')[0]
							episode_number = chunk.split('E')[1]
							if '0' in season:
								d1 = season[1:]
								d0 = season[:1]
								if d0 == 0:
									torrents[tid]['season'] = d1
								if d1 == 0:
									torrents[tid]['season'] = f"{d0}{d1}"
							if '0' in episode_number:
								d1 = episode_number[1:]
								d0 = episode_number[:1]
								if d0 == 0:
									torrents[tid]['episode_number'] = d1
								if d1 == 0:
									torrents[tid]['episode_number'] = f"{d0}{d1}"
				
				else:
					if '(' in fname and ')' in fname:
						string = fname.split('(')[1].split(')')[0]
						try:
							torrents[tid]['title'] = fname.split('(')[0].strip()
							torrents[tid]['year'] = int(string)
							if len(torrents[tid]['year']) == 4:
								torrents[tid]['files']['play_type'] = 'movies'
							else:
								torrents[tid]['files']['play_type'] = 'movies'
								if '[' in fname:
									torrents[tid]['title'] = fname.split('[')[0]
									torrents[tid]['year'] = 'Unknown'
								else:
									torrents[tid]['title'] = fname
									torrents[tid]['year'] = 'Unknown'
									torrents[tid]['files']['play_type'] = play_type
						except:
							pass

		new = torrents
		pbdl_win = create_torrent_mgr()
		active_torrents = display_torrents(torrents)
		print (active_torrents)
		pbdl_win['-TORRENT_SELECT-'].update(active_torrents)
		exit = False
		tid = None
		old = load_saved_data()
		for tid in new:
			if tid in old:
				new[tid] = old[tid]
			elif tid not in old:
				pass
				
		while True:
			if exit == True:
				break
			try:
				window, event, values = sg.read_all_windows(timeout=10)
			except Exception as e:
				log(f"Exit exception:{e}", 'error')
				exit = True
			if event=='-Close PBDL-' or event == "Exit" or event == '-DOWNLOADER_EXIT-':
					save_torrent_log(torrents)
					exit = True
					window.close()
			if event == sg.WIN_CLOSED:
				try:
					window.close()
					if exit == True:
						break
				except:
					break
			else:
				if event != '__TIMEOUT__':
					print (event)
				if event == '__TIMEOUT__':
					pass
				elif event == '-TORRENT_SELECT-':
					val = values[event][0]
					tid = int(val.split(':')[0])
					torrent_files = []
					torrent_files = get_files(tid)
					pbdl_win['-TORRENT_FILES-'].update(torrent_files)
					print (torrents)
					pbdl_win.refresh()
					#select_torrent(tid)
				elif event == 'Rotten Tomatoes Query':
					table = values['-MEDIA_TYPE-'][0]
					if table == 'movies':
						print(event, values['-3-'], play_type)
						columns = list(get_columns('movies').keys())	
						idx = columns.index('title')
						k = (f"-{idx}-")
						title = values[k]
						print ("Title:", title)
						info = get_movie_data(title)
						print ("Info", info)
					elif table == 'series':
						pragma = get_columns(table)
						columns = list(pragma.keys())
						idx = columns.index('series_name')
						k = (f"-{idx}-")
						series_name = values[k]
						idx = columns.index('season')
						k = (f"-{idx}-")
						season = values[k]
						idx = columns.index('episode_number')
						k = (f"-{idx}-")
						episode_number = values[k]
						info = get_episode_data(series_name, season, episode_number)
						print (info)
			
				#elif event == '':
				elif event == '-TORRENT_FILES-':
					#'Rick.and.Morty.S05E01.720p.WEBRip.x264-BAE.mkv'
					#Rick and Morty S04E01 Edge of Tomorty Rick Die Rickpeat.mkv
					
					_file_path = values['-TORRENT_FILES-'][0]
					print (_file_path)
					fname = _file_path.replace('.', " ")[0:len(_file_path)-4]
					sinfo = parse(fname)
					season, episode_number = se_isin(fname)
					fname.split(f"S{season}")
					series_name = fname.split(sinfo)[0].strip()
					print (f"Fname:{fname}, season:{season}, series_name:{series_name}, episode_number:{episode_number}")
					#info = tmdb_query_series(fname, series_name, season, episode_number)
					info = get_episode_data(series_name, season, episode_number)
					for k in info.keys():
						i = str(info[k])
						i = i.replace("'", "").replace('"', '')
						info[k] = i
					pragma = get_columns('series')
					columns = list(pragma.keys())
					keys = ['filepath', 'tmdbid', 'series_name', 'season', 'episode_number', 'episode_name', 'description', 'air_date', 'still_path', 'duration', 'md5', 'url']
					for k in keys:
						try:	
							pbdl_win[(f"-{columns.index(k)}-")].update(info[k])
							torrents[tid][k] = info[k]
						except Exception as e:
							print (f"Bad column: {e}")
							pass
					pbdl_win.refresh()
					save_torrent_log(torrents)
				elif event == 'be a screwball..':
					table = values['-MEDIA_TYPE-'][0]
					pragma = get_columns(table)
					columns = list(pragma.keys())
					try:
						filepath = values['-TORRENT_FILES-'][0]
					except:
						filepath = None
					sinfo = se_isin(filepath)
					print (filepath, sinfo)
					if sinfo is not None:
						season, episode_number = sinfo
					pbdl_win['-11-'].update(filepath)
					
					com = (f"find \"{SFTP_DIR}\" -type f")
					try:
						play_type = values['-MEDIA_TYPE-']
						update_media_type(play_type)
						idx = columns.index('filepath')
						key = (f"-{idx}-")
						pbdl_win[key].update(filepath)
						if tid == None:
							tid = values['-TORRENT_SELECT-'][0].split(':')[0]
						table = values['-MEDIA_TYPE-'][0]

						for column in columns:
							idx = columns.index(column)
							k = (f"-{idx}-")
							if column != 'id':					
								val = torrents[tid][column]
								pbdl_win[k].update(val)
							elif column == 'filepath':
								pbdl_win[k].update(torrents[tid]['files'])
					except:
						pass
							
				elif event == '-PBDL_SEARCH_QUERY-':
					pbdl_query = values[event]
				elif event == '-Migrate Files-':
					ret = migrate(tid)
					if conf['debug'] == True:
						log(f"Migration results:{ret}", 'info')
				elif event == '-Query TMDB-':
					play_type = values['-MEDIA_TYPE-']
					print (event, play_type)
					if play_type == 'movies':
						table = values['-MEDIA_TYPE-'][0]
						pragma = get_columns(table)
						columns = list(pragma.keys())
						idx = columns.index('title')
						k = (f"-{idx}-")
						title = values[k]
						print ("Title:", title)
						print ("Event", event)
						info = lookup_movies(title)
						if info:
							idx = columns.index('title')
							title_key = (f"-{idx}-")
							torrents[tid]['title'] = info['title']
							pbdl_win[title_key].update(info['title'])

							idx = columns.index('description')
							description_key = (f"-{idx}-")
							torrents[tid]['description'] = info['description']
							pbdl_win[description_key].update(info['description'])
						
							idx = columns.index('poster')
							poster_key = (f"-{idx}-")
							torrents[tid]['poster'] = info['poster']
							pbdl_win[poster_key].update(info['poster'])
						
							idx = columns.index('year')
							year_key = (f"-{idx}-")
							torrents[tid]['year'] = info['year']
							pbdl_win[year_key].update(info['year'])
						
							idx = columns.index('tmdbid')
							tmdbid_key = (f"-{idx}-")
							torrents[tid]['tmdbid'] = info['tmdbid']
							pbdl_win[tmdbid_key].update(info['tmdbid'])
						
							idx = columns.index('release_date')
							release_date_key = (f"-{idx}-")
							torrents[tid]['release_date'] = info['release_date']
							pbdl_win[release_date_key].update(info['release_date'])
						
							idx = columns.index('duration')
							duration_key = (f"-{idx}-")
							torrents[tid]['duration'] = info['duration']
							pbdl_win[duration_key].update(info['duration'])
						
							idx = columns.index('md5')
							md5_key = (f"-{idx}-")
							torrents[tid]['md5'] = info['md5']
							pbdl_win[md5_key].update(info['md5'])
						
							idx = columns.index('url')
							url_key = (f"-{idx}-")
							torrents[tid]['url'] = info['url']
							pbdl_win[url_key].update(info['url'])
					elif play_type == 'series':
						table = 'series'
						pragma = get_columns(table)
						columns = list(pragma.keys())
						idx = columns.index('series_name')
						k = (f"-{idx}-")
						series_name = values[k]
						idx = columns.index('season')
						k = (f"-{idx}-")
						season = values[k]
						idx = columns.index('episode_number')
						k = (f"-{idx}-")
						episode_number = values[k]
						for filepath in list(torrents[tid]['files'].keys()):
							info = tmdb_query_series(filepath, series_name, season, episode_number)
							if info:
								idx = columns.index('series_name')
								series_name_key = (f"-{idx}-")
								torrents[tid]['series_name'] = info['series_name']
								pbdl_win[series_name_key].update(info['series_name'])
						
								idx = columns.index('tmdbid')
								tmdbid_key = (f"-{idx}-")
								torrents[tid]['tmdbid'] = info['tmdbid']
								pbdl_win[tmdbid_key].update(info['tmdbid'])
							
								idx = columns.index('season')
								season_key = (f"-{idx}-")
								torrents[tid]['season'] = info['season']
								pbdl_win[season_key].update(info['season'])
								
								idx = columns.index('episode_number')
								episode_number_key = (f"-{idx}-")
								torrents[tid]['episode_number'] = info['episode_number']
								pbdl_win[episode_number_key].update(info['episode_number'])
							
								idx = columns.index('episode_name')
								episode_name_key = (f"-{idx}-")
								torrents[tid]['episode_name'] = info['episode_name']
								pbdl_win[episode_name_key].update(info['episode_name'])
							
								idx = columns.index('description')
								description_key = (f"-{idx}-")
								torrents[tid]['description'] = info['description']
								pbdl_win[description_key].update(info['description'])
							
								idx = columns.index('air_date')
								air_date_key = (f"-{idx}-")
								torrents[tid]['air_date'] = info['air_date']
								pbdl_win[air_date_key].update(info['air_date'])
								
								idx = columns.index('still_path')
								still_path_key = (f"-{idx}-")
								torrents[tid]['still_path'] = info['still_path']
								pbdl_win[still_path_key].update(info['still_path'])
							
								idx = columns.index('duration')
								duration_key = (f"-{idx}-")
								torrents[tid]['duration'] = info['duration']
								pbdl_win[duration_key].update(info['duration'])
							
								idx = columns.index('md5')
								md5_key = (f"-{idx}-")
								torrents[tid]['md5'] = info['md5']
								pbdl_win[md5_key].update(info['md5'])
							
								idx = columns.index('url')
								url_key = (f"-{idx}-")
								torrents[tid]['url'] = info['url']
								pbdl_win[url_key].update(info['url'])
						
						
				elif event == '-AUTO_REMOVE-':
					if auto_remove == True:
						auto_remove = False
					else:
						auto_remove = True
					if conf['debug'] == True:
						log(f"Auto Remove set to {auto_remove}", 'info')
				elif event == '-TORRENTS-':
					string = values[event][0].split(":")
					tid = string[0]
					for key in torrents[tid]:
						print(torrents[tid].keys())
						val = torrents[tid][key]
						k = (f"-{key}-")
						pbdl_win[k].update(val)
					
				elif event == 'Remove':
					if tid is None:
						log(f"Select a torrent file first!", 'warning')
					else:
						remove_torrent(tid)
						log(f"Torrent removed:{tid}", 'info')
				elif event == '-MEDIA_TYPE-':
					play_type = str(values[event])
					print (f"Play type changed: {play_type}")
					update_media_type(play_type)
				elif event == '-PBDL_SEARCH-':
					log("searching...", 'info')
					results = search_pb(pbdl_query, category)
					pbdl_dl_win['-PBDL_RESULTS-'].update(results)
				elif event == '-PBDL_RESULTS-':
					#try:
					picked = values[event][0]
					log(f"Downloading:{picked}", 'info')
					magnet = results[picked]
					#enable_vpn()
					com = (f"transmission-remote {conf['pbdl_url']} -a \"{magnet}\"")
					r = send_command(com)
					print (r)
					#except Exception as e:
					#	print (e)
					#	log("list empty!", 'warning')
				elif event == '-0-' or event == '-1-' or event == '-2-' or event == '-3-' or event == '-4-' or event == '-5-' or event == '-6-' or event == '-7-' or event == '-8-' or event == '-9-' or event == '-10-':
					try:
						val = values[event]
						if tid is None:
							val = values['-TORRENT_SELECT-'][0]
							tid = int(val.split(':')[0])
						ret = update_info(tid, torrents)
						log("Update info fields result:{ret}", 'info')
					except Exception as e:
						print (f"Event{event}: Not ready yet!,  sliding by crash... {e}")
						pass
				elif event == '-SET_ACTIVE-':
					info['isactive'] = int(values[event])
					pbdl_win['-0-'].update(info['isactive'])
				elif event == 'View Downloader':
					create_downloader()
				elif event  == '2 Status':
					log(f"event:2 Status:{send_command('nordvpn status')}", 'info')
				elif event == '0 Off':
					log(f"{send_command('nordvpn disonnect')}", 'info')
				elif event == '1 On':
					#enable_vpn()
					log("VPN Enabled!", 'info')
				elif event == '-SAVE_INFO-':
					print ('-SAVE_INFO-')
					#update_class_data()
					save_torrent_log(torrents)
				elif event == '-LOAD_INFO-':
					print ('-LOAD_INFO-')
					torrents = load_saved_data()
					display_torrents(torrents)
				elif event == '-REFRESH_DATA-':
					torrents = build_torrents()
					display_torrents(torrents)
				else:
					log(f"Unknown event: {event}, {values}", 'warning')
					pass
