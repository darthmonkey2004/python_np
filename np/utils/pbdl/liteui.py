import math
from np.utils.pbdl.utils import test_exists, migrate_series, migrate_movies, test_sftp_mount, mount_sftp, test_media
from np.utils.pbdl.query_series import query_series
from np.utils.pbdl.query_movies import query_movies
from np.utils.pbdl.search import search
from np.core.conf import *
from urllib.parse import quote,unquote
from np.utils.pbdl.torrentmgr import *
import json
import requests
import subprocess
import PySimpleGUI as sg
from np.utils.pbdl.pbdl import start as mgr_start
from np.core.log import np_logger
import os
log = np_logger().log_msg
win_x, win_y = None, None


def mk_torrent(filepath, target):
	com = f"transmission-create -o \"{filepath}\" \"{target}\" -t udp://tracker.coppersurfer.tk:6969/announce -t udp://tracker.openbittorrent.com:6969/announce -t udp://tracker.opentrackr.org:1337 -t udp://tracker.leechers-paradise.org:6969/announce -t udp://tracker.dler.org:6969/announce -t udp://opentracker.i2p.rocks:6969/announce -t udp://47.ip-51-68-199.eu:6969/announce -t udp://tracker.internetwarriors.net:1337/announce -t udp://9.rarbg.to:2920/announce -t udp://tracker.pirateparty.gr:6969/announce -t udp://tracker.cyberia.is:6969/announce"
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if 'done!' in ret:
		return True
	else:
		return False


def migrate():
	add_to_db()
	log(f"Migrating series files...", 'info')
	ret = migrate_series()
	if ret:
		log("Series migration finished!", 'info')
	else:
		log("Series migration failed!", 'error')
	log(f"Migrating movie files...", 'info')
	ret = migrate_movies()
	if ret:
		log("Movies migration finished!", 'info')
	else:
		log("Movies migration failed!", 'error')
	log(f"Finished!", 'info')


def getlocalip():
	i = subprocess.check_output("ifconfig", shell=True).decode().strip().split('192.168.')[1].split(' ')[0]
	return f"192.168.{i}"

def getSessionId(transmission_remote_ip=None, transmission_remote_port=9091):
	if transmission_remote_ip is None:
		transmission_remote_ip = getlocalip()
	url = f"http://{transmission_remote_ip}:{transmission_remote_port}/transmission/rpc"
	data={"method":"session-get"}
	r = requests.post(url, data=data)
	headers = {}
	headers["X-Transmission-Session-Id"] = r.text.split('<code>')[1].split('</')[0].split(' ')[1]
	return headers

def post(com=None, transmission_remote_ip=None, transmission_remote_port=9091):
	if transmission_remote_ip is None:
		transmission_remote_ip = getlocalip()
	url = f"http://{transmission_remote_ip}:{transmission_remote_port}/transmission/rpc"
	headers = getSessionId()
	r = requests.post(url, json=com, headers=headers)
	if r.status_code == 200:
		json_data = json.loads(r.text)
		return json_data
	else:
		log(f"Failed to post to url: Status Code {r.status_code}, data={r.text}", 'error')
		return None


def get_files(tid, transmission_remote_ip=None, transmission_remote_port=9091):
	if transmission_remote_ip is None:
		transmission_remote_ip = getlocalip()
	data = {"method":"torrent-get","arguments":{"fields":["files","id","activityDate","corruptEver","desiredAvailable","downloadedEver","fileStats","haveUnchecked","haveValid","peers","startDate","trackerStats"],"ids":[tid]}}
	headers = getSessionId()
	url = f"http://{transmission_remote_ip}:{transmission_remote_port}/transmission/rpc"
	r = requests.post(url, json=data, headers=headers)
	data = json.loads(r.text)
	files = []
	d = {"method":"session-get"}
	r2 = requests.post(url, json=d, headers=headers)
	d = json.loads(r2.text)
	#download_dir = d['arguments']['download-dir']
	for d in data['arguments']['torrents'][0]['files']:
		string = os.path.join(os.path.expanduser("~"), '.np', 'sftp', d['name'])
		files.append(string)
	return files





def get_torrents():
	com = {"method":"torrent-get","arguments":{"fields":["id","addedDate","name","totalSize","error","errorString","eta","isFinished","isStalled","leftUntilDone","metadataPercentComplete","peersConnected","peersGettingFromUs","peersSendingToUs","percentDone","queuePosition","rateDownload","rateUpload","recheckProgress","seedRatioMode","seedRatioLimit","sizeWhenDone","status","trackers","downloadDir","uploadedEver","uploadRatio","webseedsSendingToUs"]}}
	ret = post(com)
	keepers = ['addedDate', 'downloadDir', 'eta', 'id', 'isFinished', 'isStalled', 'name', 'peersConnected', 'percentDone', 'queuePosition', 'rateDownload', 'rateUpload', 'seedRatioLimit', 'seedRatioMode', 'status', 'totalSize', 'trackers', 'uploadRatio', 'uploadedEver']
	torrents = {}
	for t in ret['arguments']['torrents']:
		tid = t['id']
		torrents[tid] = {}
		for key in keepers:
			torrents[tid][key] = t[key]
	return torrents


def get_series_info(filepath, window_title='Enter Series Info', series_name=None, episode_number=None, season=None):
	layout = []
	user_input = None
	fname_line = [sg.Text(filepath)]
	series_name_line = [sg.Text('Series Name'), sg.Input(default_text=series_name, enable_events=True, change_submits=True, do_not_clear=True, key='-SERIES_NAME-', expand_x=True)]
	season_line = [sg.Text('Season'), sg.Input(default_text=season, enable_events=True, change_submits=True, do_not_clear=True, key='-SEASON-', expand_x=True)]
	episode_number_line = [sg.Text('Episode Number'), sg.Input(default_text=episode_number, enable_events=True, change_submits=True, do_not_clear=True, key='-EPISODE_NUMBER-', expand_x=True)]
	output_line = [sg.Text('', key='-OUTPUT-')]
	submit = [sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-SUBMIT-')]
	layout.append(fname_line)
	layout.append(series_name_line)
	layout.append(season_line)
	layout.append(episode_number_line)
	layout.append(output_line)
	layout.append(submit)
	win = sg.Window(window_title, layout, keep_on_top=False, element_justification='center', finalize=True)
	while True:
		event, values = win.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-SUBMIT-':
			if series_name is not None and season is not None and episode_number is not None:
				win.close()
			else:
				win['-OUTPUT-'].update('Error: Ensure all fields complete before continuing!')
		elif event == '-SERIES_NAME-':
			series_name = values[event]
			win['-OUTPUT-'].update(f"series_name set:{series_name}!")
		elif event == '-SEASON-':
			try:
				season = int(values[event])
				win['-OUTPUT-'].update(f"Season set:{season}!")
			except Exception as e:
				win['-OUTPUT-'].update(f"Error setting season:{e}!")
				season = None
		elif event == '-EPISODE_NUMBER-':
			try:
				episode_number = int(values[event])
				win['-OUTPUT-'].update(f"Episode Number set:{episode_number}!")
			except Exception as e:
				win['-OUTPUT-'].update(f"Error setting season:{e}!")
				episode_number = None
	return 'series', series_name, season, episode_number


def get_movie_info(filepath, title=None, year=None, window_title='Enter Series Info'):
	layout = []
	user_input = None
	fname_line = [sg.Text(filepath)]
	title_line = [sg.Text('Title'), sg.Input(default_text=title, enable_events=True, change_submits=True, do_not_clear=True, key='-TITLE-', expand_x=True)]
	year_line = [sg.Text('Year'), sg.Input(default_text=year, enable_events=True, change_submits=True, do_not_clear=True, key='-YEAR-', expand_x=True)]
	output_line = [sg.Text('', key='-OUTPUT-')]
	submit = [sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-SUBMIT-')]
	layout.append(fname_line)
	layout.append(title_line)
	layout.append(year_line)
	layout.append(output_line)
	layout.append(submit)
	win = sg.Window(window_title, layout, keep_on_top=False, element_justification='center', finalize=True)
	while True:
		event, values = win.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-SUBMIT-':
			if year is None:
				year = 0000
			if title is not None:
				win.close()
			else:
				win['-OUTPUT-'].update('Error: Ensure all fields complete before continuing!')
		elif event == '-TITLE-':
			title = values[event]
			win['-OUTPUT-'].update(f"title set:{title}!")
		elif event == '-YEAR-':
			try:
				year = int(values[event])
				win['-OUTPUT-'].update(f"Year set:{year}!")
			except Exception as e:
				win['-OUTPUT-'].update(f"Error setting year:{e}!")
				year = None
	return 'movies', title, year


def get_play_type(filepath, play_type=None, title=None, year=None, series_name=None, season=None):
	if title is not None:
		play_type = 'movies'
		data = get_movie_info(filepath=filepath, title=title, year=None)
	elif series_name is not None:
		play_type = 'series'
		data = get_series_info(filepath, series_name=series_name, episode_number=None, season=season)
	elif title is None and series_name is None:
		data = get_series_info(filepath)
	else:
		layout = []
		window_title = 'Select play type:'
		fname_line = [sg.Text(f"Setting info for:{filepath}...")]
		play_type_combo = [sg.Combo(['series', 'movies', 'music'], 'series', enable_events=True,key='-PLAY_TYPE-')]
		layout.append(play_type_combo)
		win = sg.Window(window_title, layout, size=(300, 50), keep_on_top=False, element_justification='center', finalize=True)
		data = None
		while True:
			event, values = win.read()
			if event == sg.WIN_CLOSED:
				break
			else:
				play_type = values[event]
				win.close()
				if play_type == 'series':
					data = get_series_info(filepath)
				elif play_type == 'movies':
					data = get_movie_info(filepath)
				elif play_type == 'music':
					print("Whoops, incomplete!")
					return play_type
	log(f"data:{data}", 'info')
	return data




def add_to_db():
	string = None
	is_mounted = test_sftp_mount()
	if is_mounted is False:
		mount_sftp()
	extensions = ['.mp4', '.mov', '.wmv', '.avi', '.flv', '.f4v', '.swf', '.mkv', '.mpeg-2']
	torrents = get_torrents()
	for tid in torrents:
		series_name = None
		season = None
		episode_number = None
		title = None
		year = None
		log(f"Tid: {tid}", 'info')
		if not torrents[tid]['isFinished']:
			pass
		else:
			files = get_files(tid)
			for filepath in files:
				fname = os.path.basename(filepath)
				play_type = test_media(fname)
				print(f"fname:{fname}, play_type:{play_type}")
				ext = os.path.splitext(fname)[1]
				if ext.lower() in extensions:
					try:
						if play_type == 'series':
							series_name, season, episode_number = test_media(fname, True)
							series_name = series_name.capitalize()
							info = query_series(series_name, season, episode_number)
						elif play_type == 'movies':
							title, year = test_media(fname)
							info = query_movies(title)
						elif play_type == 'music':
							pass
					except Exception as e:
						if series_name is not None:
							data = get_play_type(filepath=filepath, play_type='series', series_name=series_name, season=season)
						elif title is not None:
							data = get_play_type(filepath=filepath, play_type='movies', title=title)
						else:
							data = get_play_type(filepath=filepath)
						
						play_type = data[0]
						if play_type == 'series':
							series_name, season, episode_number = data[1], data[2], data[3]
							if season is not None:
								season = int(season)
							if episode_number is not None:
								episode_number = int(episode_number)
							try:
								info = query_series(series_name, season, episode_number)
							except Exception as e:
								log(f"Unable to get info for torrent id:{tid}! ({e})", 'error')
								return False
						elif play_type == 'movies':
							title, year = data[1], data[2]
							info = query_movies(title)
						elif play_type == 'music':
							pass
					vals = []
					keys = []
					pragma = get_columns(play_type)
					columns = list(pragma.keys())
					for column in columns:
						if column != 'id':
							keys.append(str(column))
							if column == 'isactive':
								vals.append("1")
							elif column == 'filepath':
								fullpath = filepath.replace("'", "%27")
								log(f"Adding file: {fullpath}", 'info')
								vals.append(f"\'{fullpath}\'")
							else:
								try:
									dtype = pragma[column]['data_type']
									val = info[column]
									if val is None or val == '':
										if dtype == 'TEXT':
											val = 'Unknown'
										elif dtype == 'INTEGER' or dtype == 'BOOL':
											val = 0
									else:	
										if dtype == 'TEXT':
											val = val.replace('"', '').replace("'", "")
											vals.append(f"\'{val}\'")
										elif dtype == 'INTEGER' or dtype == 'BOOL':
											vals.append(str(val))
								except Exception as e:
									log(f"Exception {e}: Column:{column}", 'error')
									val = 'Unknown'
									vals.append(f"\'{val}\'")
					j = ', '
					kstring = j.join(keys)
					vstring = j.join(vals)
					qstring = (f"INSERT INTO {play_type} ({kstring}) VALUES({vstring});")
					dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
					com = f"sqlite3 \"{dbfile}\" \"{qstring}\""
					ret = subprocess.check_output(com, shell=True).decode().strip()
					if ret:
						log(f"Error: Add to database failed for file '{filepath}': {ret}", 'error')
					else:
						log("Ok!")


def secs_to_mins(secs):
	mins = secs / 60
	secs = round(float(f".{round(float(str(mins).split('.')[1]))}") * 60)
	return mins, secs


def mins_to_hrs(mins):
	hrs = mins / 60
	mins = float(f".{str(hrs).split('.')[1]}") * 60
	secs = round(float(f".{str(mins).split('.')[1]}") * 60)
	mins = int(str(mins).split('.')[0])
	return hrs, mins, secs

def hrs_to_days(hrs):
	days = hrs / 24

def convert_eta(eta):
	mins, secs = secs_to_mins(eta)
	if mins > 60:
		hrs, mins, secs = mins_to_hrs(mins)
		if hrs > 24:
			
			days = hrs / 24
			r = float(f".{str(hrs).split('.')[1]}")
			days = float(str(days).split('.')[0])
			hrs = round(r * 60)
			hrs = r * 24
			days = round(days)
			hrs = round(hrs)
			return f"{days} days, {hrs} hours"
		else:
			mins = round(mins)
			secs = round(secs)
			hrs = round(hrs)
			return f"{hrs}:{mins}:{secs}"
	else:
		mins = round(mins)
		secs = round(secs)
		return f"0:{mins}:{secs}"


def convert_rate(rate):
	kb = round(rate / 1024)
	if kb <= 1000:
		return f"{kb} KBps"
	else:
		mb = round(kb / 1024)
		if mb <= 1000:
			return f"{mb} MBps"
		else:
			gb = round(mb / 1024)
			return f"{gb} GBps"


def convert_size(size_bytes):
	if size_bytes == 0:
		return "0B"
	size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(math.floor(math.log(size_bytes, 1024)))
	p = math.pow(1024, i)
	s = round(size_bytes / p, 2)
	return "%s %s" % (s, size_name[i])


def update_info(data=None):
	if data is None:
		data = get_torrents()
	info = {}
	for tid in data.keys():
		percent = round(float(data[tid]['percentDone']) * 100, 2)
		eta = convert_eta(data[tid]['eta'])
		rate = convert_rate(data[tid]['rateDownload'])
		s = int(data[tid]['status'])
		status = 'Stopped'
		if s == 0:
			status = 'Stopped'
		elif s == 1:
			log("Status unknown! 1", 'warning')
		elif s == 2:
			log("Status unknown! 2", 'warning')
		elif s == 3:
			status = f"Queued:{data[tid]['queuePosition']}"
		elif s == 4:
			status = 'Downloading'
		size = convert_size(int(data[tid]['totalSize']))
		string = f"Status:{status}, Percent:{percent}%, ETA:{eta}, Download Rate:{rate}, Peers:{data[tid]['peersConnected']}, Size:{size}, Name:{data[tid]['name']}"
		info[tid] = string
	return info


def gui(info):
	try:
		win_x, win_y = load_win_location()
	except:
		win_x, win_y = 510, 1000
		save_win_location(win_x, win_y)
	layout = []
	results = []
	conf = readConf()
	play_type_combo = [sg.Combo(['series', 'movies', 'music'], conf['play_type'] , enable_events=True,key='-DL_MEDIA_TYPE-'), sg.Checkbox(text="VPN On/Off", auto_size_text=True, change_submits=True, enable_events=True, key='-TOGGLE_VPN-'), sg.Text('Public IP Address:'), sg.Text('', key='-PUBLIC_IP-')]
	layout.append(play_type_combo)
	search_line = [sg.Text('Enter search query here:'), sg.Input('', enable_events=True, change_submits=True, key='-PBDL_SEARCH_QUERY-', expand_x=True), sg.Button('Search', key='-PBDL_SEARCH-'), sg.Button('Quit!', key='-DOWNLOADER_EXIT-')]
	layout.append(search_line)
	results_box = [sg.Listbox(values=results, change_submits=True, size = (200, 10), auto_size_text=False, enable_events=True, expand_x=False, expand_y=False, key='-PBDL_RESULTS-')]
	layout.append(results_box)
	#torrent_info_box = [sg.Listbox([], select_mode = None, change_submits = True, enable_events = True, size = (None, None), auto_size_text = True, key = '-TORRENT_INFO-', expand_x = True, expand_y = True)]
	torrent_info_box = []
	for tid in list(info.keys()):
		line = [sg.Radio(tid, key=f"-{tid}-", group_id=0, enable_events=True), sg.Text(key=f"info-{tid}")]
		torrent_info_box.append(line)
	torrent_info_box.append(sg.Radio('all', key='-ALL-', group_id=0, enable_events=True))
	layout.append(torrent_info_box)
	magnet_line = [sg.Text('Enter magnet link here:'), sg.Input('', key='-MAGNET-', enable_events=True), sg.Button('Add')]
	layout.append(magnet_line)
	buttons = [sg.Button('Start!'), sg.Button('Stop'), sg.Button('Remove'), sg.Button('Delete'), sg.Button('Manager'), sg.Button('Migrate Files')]
	layout.append(buttons)
	output_box = [sg.Multiline(default_text = "", enter_submits = True, disabled = False, autoscroll = True, border_width = None, size = (200, 40), auto_size_text = None, background_color = None, text_color = None, horizontal_scroll = False, change_submits = True, enable_events = True, do_not_clear = True, key = '-OUTPUT-', write_only = False, auto_refresh = True, reroute_stdout = True, reroute_stderr = True, reroute_cprint = True, echo_stdout_stderr = True, justification = 'left', no_scrollbar = False, expand_x = False, expand_y = False, rstrip = True)]
	layout.append(output_box)
	win = sg.Window(title='Torrent Info', layout=layout, size = (1100, 600), location = (win_x, win_y))
	win.finalize()
	return win

def add(magnet, paused=False, download_dir="/var/lib/transmission-daemon/downloads"):
	com = {}
	com['method'] = "torrent-add"
	com['arguments'] = {}
	if not paused:
		paused = 'false'
	elif paused:
		paused = 'true'
	com['arguments']['paused'] = paused
	com['arguments']['download-dir'] = download_dir
	com['arguments']['filename'] = magnet
	post(com)


def start():
	global win_x, win_y
	info = update_info()
	try:
		win_x, win_y = load_win_location()
		win = gui(info)
		t = torrent_mgr(win)
	except:
		win = gui(info)
		t = torrent_mgr(win)
		win_x, win_y = win.current_location()
		save_win_location(win_x, win_y)
	return t, info, win, win_x, win_y


def load_win_location(filepath='/home/monkey/.np/tmgr_location.txt'):
	with open(filepath, 'r') as f:
		win_x, win_y = f.read().split(':')
		f.close()
	log(f"Window location loaded! x={win_x}, y={win_y}", 'info')
	return int(win_x), int(win_y)

def save_win_location(x, y, filepath='/home/monkey/.np/tmgr_location.txt'):
	with open(filepath, 'w') as f:
		data = f"{x}:{y}"
		f.write(data)
		f.close()
	log(f"Window location saved! x={x}, y={y}", 'info')
#com = {"method":"session-stats"}

def send(com):
	com = f"{com} 2>/dev/null"
	try:
		ret = subprocess.check_output(com, timeout=2, shell=True).decode().strip()
		if ret == '':
			ret = None
		return ret
	except Exception as e:
		#print("Command failed:", e)
		return None


def get_gateway():
	return send(com = "route -n | grep \"0.0.0.0\" | grep -v \"255.255\"").split('0.0.0.0 ')[1].strip()


def test_vpn_status():
	try:
		ret = send(f"pgrep openvpn").split("\n")
	except:
		ret = []
	if len(ret) == 0:
		return False
	elif len(ret) >= 1:
		return True


def test_vpn():
	active = test_vpn_status()
	if active:
		return True
	else:
		print("VPN Not enabled!")
		return False


def check_active_downloads():
	data = get_torrents()
	for tid in data.keys():
		status = int(data[tid]['status'])
		if status != 0:
			return True
		else:
			pass
	return False

def ensure_safe_downloads(t, win):
	have_active = check_active_downloads()
	if have_active:
		vpn_active = test_vpn()
		win['-TOGGLE_VPN-'].update(vpn_active)
		if not vpn_active:
			log(f"VPN not enabled and torrents are downloading! Executing stop all...", 'warning')
			t.stop_all()
			return False
		else:
			return True
	else:
		return True

#data = {"method":"torrent-stop","arguments":{"ids":[2]}}
def run_ui():
	t, info, win, win_x, win_y = start()
	win['-TOGGLE_VPN-'].update(t.vpn_status())
	pos = 0
	ct = 1500
	active = None
	magnet = None
	exit = False
	while True:
		if exit:
			win_x, win_y = win.current_location()
			save_win_location(win_x, win_y)
			break
		pos += 1
		window, event, values = sg.read_all_windows(timeout=1)
		if event != '__TIMEOUT__':
			#print("event:", event)
			if event == 'Start!':
				if active is None:
					t.start_all()
					log("Started all!", 'info')
				else:
					t.start(active)
					log("Started id: {active}", 'info')
			elif event == 'Stop':
				if active is None:
					t.stop_all()
					log("Stopped all!", 'info')
				else:
					t.stop(active)
					log("Stopped id: {active}", 'info')
			elif event == '-MAGNET-':
				magnet = unquote(values[event])
				win['-MAGNET-'].update(magnet)
			elif event == 'Add':
				add(magnet)
				log(f"adding magnet: {magnet}", 'info')
				win.close()
				t, info, win, win_x, win_y = start()
			elif event == 'Delete':
				if active is not None:
					t.remove_and_delete(active)
					log(f"Deleted id (plus data): {active}", 'info')
					win.close()
					t, info, win, win_x, win_y = start()
				else:
					log("Cannot delete all!", 'warning')
			elif event == 'Remove':
				if active is not None:
					t.remove(active)
					log(f"Removed id: {active}", 'info')
					win.close()
					t, info, win, win_x, win_y = start()
				else:
					log(f"cannot remove all!", 'warning')
			elif event == 'Manager':
				mgr_start()
			elif event == sg.WIN_CLOSED or event=='-Close PBDL-' or event == "Exit" or event == '-DOWNLOADER_EXIT-':
				exit = True
			elif event == '-DL_MEDIA_TYPE-':
				play_type = values[event]
				log(f"Play type set: {play_type}", 'info')
			elif event == '-PBDL_SEARCH-':
				log(f"pbdl.downloader():searching {pbdl_query}...", 'info')
				results = search(pbdl_query)
				window['-PBDL_RESULTS-'].update(results)

			elif event == '-PBDL_SEARCH_QUERY-':
				pbdl_query = values[event]
			elif event == '-TOGGLE_VPN-':
				state = t.vpn_status()
				print(event, state)
				if not state:
					log("Starting vpn...", 'info')
					t.start_vpn()
					log("VPN Started!", 'info')
				else:
					log("Stopping vpn...", 'info')
					t.stop_vpn()
					log("VPN Stopped!", 'info')
			elif event == '-PBDL_RESULTS-':
				try:
					picked = values[event][0]
					log(f"pbdl.downloader():Downloading:{picked}", 'info')
					magnet = results[picked]['magnet']
					magnet = unquote(magnet)
					win['-MAGNET-'].update(magnet)
				except Exception as e:
					log(f"pbdl.downloader():list empty? {e}", 'error')
			elif event == 'Migrate Files':
				migrate()
			elif event == 'VID_OUT':
				pass
			elif event == '-ALL-':
				active = 'all'
				log("Selected: 'all'...", 'info')
			else:
				try:
					active = int(event.split('-')[1])
					log(f"Selected: {active}", 'info')
				except Exception as e:
					log(f"can't parse key: {e} event: {event}", 'error')
		if pos == ct:
			win['-PUBLIC_IP-'].update(t.get_public_ip())
			pos = 0
			info = update_info()
			for tid in info.keys():
				try:
					key = f"-{tid}-"
					win[f"info-{tid}"].update(info[tid])
				except Exception as e:
					log("Error updating window: {e}", 'error')
			ensure_safe_downloads(t, win)
		win.refresh()
	win.close()


if __name__ == "__main__":
	run_ui()
