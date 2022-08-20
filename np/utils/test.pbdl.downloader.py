def search_pb(query, cat=200):
	results = {}
	if conf['debug'] == True:
		np.log("Searching using html function (search_pb)...", 'info')
		query = quote(query)
		base_url = get_url()
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
	



def get_url():
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
	


def create_downloader():
	search_line = [sg.Input('Enter search query here:', enable_events=True, change_submits=True, key='-PBDL_SEARCH_QUERY-', expand_x=True), sg.Button('Search', key='-PBDL_SEARCH-'), sg.Button('Quit!', key='-DOWNLOADER_EXIT-')]
	results_box = [sg.Listbox(values=results, change_submits=True, auto_size_text=True, enable_events=True, expand_x=True, expand_y=True, key='-PBDL_RESULTS-')]
	pbdl_search_layout = [
		[search_line],
		[results_box]
	]
	try:
		x = 0
		y = conf['windows']['pbdl_dl']['y']
		w = conf['windows']['pbdl_dl']['w']
		h = conf['windows']['pbdl_dl']['h']
	except:
		conf = np.readConf()
		screen = conf['screen']
		x, y = conf['screens'][screen]['pos_x'], conf['screens'][screen]['pos_y']
		try:
			test = conf['windows']
		except:
			pass
		w = conf['windows']['pbdl_dl']['w']
		h = conf['windows']['pbdl_dl']['h']
		np.writeConf(conf)
	pbdl_dl_win = sg.Window('GUI', pbdl_search_layout, no_titlebar=False, location=(x,y), size=(w,h), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
	downloader = True
	return pbdl_dl_win


def create_torrent_mgr():
	play_type = conf['play_type']
	menu_def = [['&File', ['E&xit']], ['&Toolbar', ['&Remove Torrent', '&Delete Torrent', '&Query TMDB', 'VPN', ['&0 Off', '&1 On', '&2 Status'], 'View &Downloader']], ['&Help', '&About...']]
	columns_list = list(np.get_columns(play_type).keys())
	pbdl_layout = [
	[sg.Listbox(active_torrents, expand_x=True, enable_events=True, size=(50,10), key='-TORRENT_SELECT-')],
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
	title_bar_layout = [sg.MenubarCustom(menu_def, tearoff=False, key='-menubar_key-'), sg.Combo(['series', 'movies', 'music'], conf['play_type'] , enable_events=True,key='-MEDIA_TYPE-'), sg.Button("Quit!", key='-Close PBDL-')],
	title_bar_frame = sg.Frame(title='', layout = title_bar_layout, key='title_bar_frame', expand_x=True, grab=True, element_justification="center", vertical_alignment="top")
	media_info_layout = []
	is_active_ckbox = [sg.Button('Refresh From Remote', key='-REFRESH_DATA-'), sg.Button('Load Info', key='-LOAD_INFO-'), sg.Button('Save Info', key='-SAVE_INFO-'), sg.Checkbox(text='Is Active:', auto_size_text=True, change_submits=True, enable_events=True, key='-SET_ACTIVE-'), sg.Checkbox(text='Auto Remove Torrents:', auto_size_text=True, change_submits=True, enable_events=True, key='-AUTO_REMOVE-')]
	media_info_layout.append(is_active_ckbox)
	pos = -1
	for column in columns_list:
		pos = pos + 1
		d = ("d_" + str(pos))
		k = ("-" + str(pos) + "-")
		line = [sg.Text(column, key=d), sg.Input(default_text='', enable_events=True, do_not_clear=True, key=k, expand_x=True)]
		media_info_layout.append(line)
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
		conf = np.readConf()
		screen = conf['screen']
		x, y = conf['screens'][screen]['pos_x'], conf['screens'][screen]['pos_y']
		w = conf['windows']['pbdl_dl']['w']
		h = conf['windows']['pbdl_dl']['h']
	pbdl_win = sg.Window('GUI', layout, no_titlebar=False, location=(x,y), size=(600,900), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
	torrent_mgr = True
	return torrent_mgr


def remove_torrent(_id):
	com = (f"transmission-remote {conf['pbdl_url']} -t{_id} -rad")
	ret = send_command(com)
	#build_torrents()
	return ret

