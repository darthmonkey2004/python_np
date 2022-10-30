import sys
from np.core.conf import readConf, writeConf
import PySimpleGUI as sg
from np.core.log import np_logger
from np.utils.pbdl.search import search
from np.core.core import shell
from np.utils.pbdl.torrentmgr import torrent_mgr

logger = np_logger().log_msg

def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)


def create_downloader():
	global results
	conf = readConf()
	play_type = conf['play_type']
	results = []
	play_type_combo = [sg.Combo(['series', 'movies', 'music'], conf['play_type'] , enable_events=True,key='-DL_MEDIA_TYPE-')]
	search_line = [sg.Input('Enter search query here:', enable_events=True, change_submits=True, key='-PBDL_SEARCH_QUERY-', expand_x=True), sg.Button('Search', key='-PBDL_SEARCH-'), sg.Button('Quit!', key='-DOWNLOADER_EXIT-')]
	results_box = [sg.Listbox(values=results, change_submits=True, auto_size_text=True, enable_events=True, expand_x=True, expand_y=True, key='-PBDL_RESULTS-')]
	pbdl_search_layout = [
		[play_type_combo],
		[search_line],
		[results_box]
	]
	try:
		x, y = conf['locations']['dl']
		w = conf['windows'][conf['screen']]['pbdl_dl']['w']
		h = conf['windows'][conf['screen']]['pbdl_dl']['h']
	except Exception as e:
		log(f"Error: Unable to restore previous window location: {e}", 'error')
		conf = readConf()
		screen = conf['screen']
		x, y = conf['windows'][conf['screen']]['pbdl_dl']['x'], conf['windows'][conf['screen']]['pbdl_dl']['y']
		try:
			test = conf['windows']
		except:
			pass
		w = conf['windows'][conf['screen']]['pbdl_dl']['w']
		h = conf['windows'][conf['screen']]['pbdl_dl']['h']
		writeConf(conf)
	win = sg.Window('PBDL Downloader', pbdl_search_layout, no_titlebar=False, location=(x,y), size=(w,h), keep_on_top=False, grab_anywhere=True, element_justification='center', finalize=True, resizable=True).Finalize()
	return win

def get_location(win):
	return win.current_location()


def downloader_loop(win=None, mgr=None):
	conf = readConf()
	exit = False
	if mgr == None:
		mgr = torrent_mgr()
	if win == None:
		win = create_downloader()
	mgr.set_start_paused()
	mgr.set_global_ratio(0)
	mgr.start_vpn()
	while True:
		if exit == True:
			break
		try:
			window, event, values = sg.read_all_windows(timeout=10)
			if window is not None:
				conf['locations']['dl'] = window.current_location()
		except Exception as e:
			log(f"Exit exception:{e}", 'error')
			exit = True
		if event != '__TIMEOUT__':
			if conf['debug'] == True:
				log(f"EVENT: {event}", 'info')
		if event=='-Close PBDL-' or event == "Exit" or event == '-DOWNLOADER_EXIT-':
				exit = True
				conf['locations']['dl'] = window.current_location()
				writeConf(conf)
				window.close()
		if event == '-DL_MEDIA_TYPE-':
			play_type = values[event]
		if event == sg.WIN_CLOSED:
			try:
				window.close()
				if exit == True:
					break
			except:
				break
		else:
			if event == '-PBDL_SEARCH-':
				log(f"searching {pbdl_query}...", 'info')
				results = search(pbdl_query)
				window['-PBDL_RESULTS-'].update(results)

			elif event == '-PBDL_SEARCH_QUERY-':
				pbdl_query = values[event]
			elif event == '-PBDL_RESULTS-':
				try:
					picked = values[event][0]
					log(f"Downloading:{picked}", 'info')
					magnet = results[picked]
					ret = mgr.add(magnet)
					mgr.stop_seeds()
					if ret != '':
						log(f"Send magnet results: {ret}", 'info')
				except Exception as e:
					log(f"list empty? {e}", 'warning')
		win.refresh()
	return True


def quit(win):
	conf['locations']['dl'] = win.current_location()
	writeConf(conf)
	try:
		win.close()
	except:
		pass


def start(mgr=None, win=None):
	if mgr == None:
		mgr = torrent_mgr()
	if win == None:
		win = create_downloader()
	ret = downloader_loop(win, mgr)
	if ret:
		return
