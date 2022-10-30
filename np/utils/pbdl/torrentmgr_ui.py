import PySimpleGUI as sg
from np.core.nplayer_db import get_columns
from np.core.conf import readConf


def create_torrentmgr_ui():
	conf = readConf()
	play_type = conf['play_type']
	UI_OPTS = ['Refresh Torrents', 'Save', 'Load', 'Clear Data', 'Query Database', 'Add To Sql', 'Set Media Type', 'Migrate Data', 'Add Torrent', 'Remove', 'Remove and Delete', 'Stop All', 'Start All', 'Set Remote Host', 'View Downloader', 'Exit', 'Set Wait Task', 'Search Rotten Tomatoes', 'Search TMDB', 'VPN Off', 'VPN On', 'VPN Status']
	active_torrents = []
	menu_def = [
		['Control:', ['Data', ['Refresh Torrents', 'Save', 'Load', 'Clear Data'], ['Database', ['Set Media Type', ['series', 'movies', 'music'], 'Add To Sql', 'Migrate Data']]]],
		['Torrents:', ['Actions', ['Add Torrent', 'Remove', 'Remove and Delete', 'Stop All', 'Start All']]],
		['Tools:', ['Set Remote Host', 'View Downloader', 'Exit', 'Set Wait Task']],
		['Lookup Services:', ['Set Api Key:Rotten Tomatoes', 'Set Api Key:Search TMDB']],
		['VPN:', ['VPN Off', 'VPN On', 'VPN Status']]
		
	]
	columns_list = list(get_columns(play_type).keys())
	pbdl_layout = [
	[sg.Listbox(active_torrents, expand_x=True, enable_events=True, size=(50,10), key='-TORRENT_SELECT-')],
	[sg.Text('tid:'), sg.Text('', expand_x=True, key='tid')],
	[sg.Text('Name:'), sg.Text('', expand_x=True, key='name')],
	[sg.Text('Percent:'), sg.Text('', expand_x=True, key='percent')],
	[sg.Text('Size Unit:'), sg.Text('', expand_x=True, key='size_unit')],
	[sg.Text('Have:'), sg.Text('', expand_x=True, key='have')],
	[sg.Text('ETA:'), sg.Text('', expand_x=True, key='eta')],
	[sg.Text('Upload Rate:'), sg.Text('', expand_x=True, key='upload_rate')],
	[sg.Text('Download Rate:'), sg.Text('', expand_x=True, key='download_rate')],
	[sg.Text('Status:'), sg.Text('', expand_x=True, key='status')],
	[sg.Text('Ratio:'), sg.Text('', expand_x=True, key='ratio')],

	]
	title_bar_layout = [sg.MenubarCustom(menu_def, tearoff=False, key='-menubar_key-'), sg.Combo(['series', 'movies', 'music'], conf['play_type'] , enable_events=True,key='-MEDIA_TYPE-'), sg.Button("Quit!", key='-QUIT_PBDL-')],
	title_bar_frame = sg.Frame(title='', layout = title_bar_layout, key='title_bar_frame', expand_x=True, grab=True, element_justification="center", vertical_alignment="top")
	media_info_layout = build_column_table(play_type)
	media_info_layout.append([sg.Listbox([], size=(10,10), expand_x=True, expand_y=False, enable_events=True, select_mode='multiple', key='-TORRENT_FILES-')])
	media_info_actions = [sg.Combo(['-rotten tomatoes-', '-TMDB-', '-IMDB-'], '-TMDB-' , enable_events=True, key='-LOOKUP_TYPE-'), sg.Button('Lookup!', key='-LOOKUP-'), sg.Button('Migrate Files', key='-Migrate Files-'), sg.Button('Remove'), sg.Button('Remove+Delete'), sg.Button('Exclude')]
	media_info_layout.append(media_info_actions)
	info_frame = sg.Frame(title='Torrent Data', layout=pbdl_layout, key='info_frame', expand_x=True, grab=True, element_justification="left", vertical_alignment="top")
	media_info_frame = sg.Frame(title='Media Info', layout=media_info_layout, key='media_info_frame', expand_x=True, grab=True, element_justification="right", vertical_alignment="top")
	layout = [[title_bar_frame], [info_frame, [media_info_frame, sg.Sizegrip(key='-gui_size-')]]]
	screen = conf['screen']
	if screen == 0:
		screen = 1
	elif screen == 1:
		screen = 0
	try:
		x = int(conf['windows'][screen]['pbdl']['x'])
		y = int(conf['windows'][screen]['pbdl']['y'])
		w = int(conf['windows'][screen]['pbdl']['w'])
		h = (int(conf['windows'][screen]['pbdl']['h']) + 100)
	except:
		conf = readConf()
		screen = conf['screen']
		x, y = conf['windows'][screen]['pbdl']['x'], conf['windows'][screen]['pbdl']['y']
		w = conf['windows'][screen]['pbdl']['w']
		h = conf['windows'][screen]['pbdl']['h']
	pbdl_win = sg.Window('Torrent Manager', layout, no_titlebar=False, location=(x,y), size=(1024,900), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
	return pbdl_win


def build_column_table(play_type=None):
	conf = readConf()
	if play_type == None:
		play_type = conf['play_type']
	media_info_layout = []
	is_active_ckbox = [sg.Button('Refresh From Remote', key='-REFRESH_DATA-'), sg.Button('Load Info', key='-LOAD_INFO-'), sg.Button('Save Info', key='-SAVE_INFO-'), sg.Checkbox(text='Is Active:', auto_size_text=True, change_submits=True, enable_events=True, key='-SET_ACTIVE-'), sg.Checkbox(text='Auto Remove Torrents:', auto_size_text=True, change_submits=True, enable_events=True, key='-AUTO_REMOVE-')]
	media_info_layout.append(is_active_ckbox)
	pos = -1
	columns = list(get_columns(play_type).keys())
	keys = []
	for pos in range(0, 14):
		k = f"dbcolumn{pos}"
		keys.append(k)
	pos = -1
	p1 = None
	p2 = None
	for k in keys:
		pos += 1
		if p1 is None:
			p1 = pos
			try:
				column1 = columns[pos]
			except:
				column1 = "None"
		else:
			p2 = pos
			try:
				column2 = columns[pos]
			except:
				column2 = None
			line = [sg.Text(column2, key=f"-dbcolumn{p1}-"), sg.Input(default_text='', enable_events=True, do_not_clear=True, key=f"dbcolumn{p1}", expand_x=True), sg.Text(column1, key=f"-dbcolumn{p2}-"), sg.Input(default_text='', enable_events=True, do_not_clear=True, key=f"dbcolumn{p2}", expand_x=True)]
			media_info_layout.append(line)
			p1 = None
			p2 = None
	return media_info_layout


