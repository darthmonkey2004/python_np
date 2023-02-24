import PySimpleGUI as sg
import json
import os
import requests
from np.core.conf import readConf
from np.core.log import np_logger
from np.utils.pbdl.utils import test_media
from np.utils.pbdl.liteui import *
from np.core.nplayer_db import get_columns
from np.utils.cleandb import run as cleandb

log = np_logger().log_msg
conf = readConf()
DATA_DIR = os.path.join(os.path.expanduser("~"), '.np')
SFTP_DIR = os.path.join(DATA_DIR, 'sftp')
HOME = os.path.expanduser("~")


def getSessionId(transmission_remote_ip='192.168.1.2', transmission_remote_port=9091):
	url = f"http://{transmission_remote_ip}:{transmission_remote_port}/transmission/rpc"
	data={"method":"session-get"}
	r = requests.post(url, data=data)
	headers = {}
	headers["X-Transmission-Session-Id"] = r.text.split('<code>')[1].split('</')[0].split(' ')[1]
	return headers


def get_files(tid, transmission_remote_ip='192.168.1.2', transmission_remote_port=9091):
	extensions = ['.mp4', '.mov', '.wmv', '.avi', '.flv', '.f4v', '.swf', '.mkv', '.mpeg-2']
	data = {"method":"torrent-get","arguments":{"fields":["files","id","activityDate","corruptEver","desiredAvailable","downloadedEver","fileStats","haveUnchecked","haveValid","peers","startDate","trackerStats"],"ids":[tid]}}
	headers = getSessionId(transmission_remote_ip, transmission_remote_port)
	url = f"http://{transmission_remote_ip}:{transmission_remote_port}/transmission/rpc"
	r = requests.post(url, json=data, headers=headers)
	data = json.loads(r.text)
	files = []
	d = {"method":"session-get"}
	r2 = requests.post(url, json=d, headers=headers)
	d = json.loads(r2.text)
	for d in data['arguments']['torrents'][0]['files']:
		string = d['name']
		_, ext = os.path.splitext(string)
		if ext in extensions:
			files.append(string)
			#log(f"liteui.get_files():Added file - '{string}'", 'info')
	return files


def get_fullpath(filepath):
	com = f""
	#allfiles = ssh(com)
	com = f"ssh monkey@192.168.1.2 'find \"/var/lib/transmission-daemon/downloads\" -name \"*.*\"'"
	allfiles = subprocess.check_output(com, shell=True).decode().strip().splitlines()
	fullpath = None
	for item in allfiles:
		if filepath in item or filepath == item:
			fullpath = item
	return fullpath

	

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
	win_key = window_title.lower().replace(' ', '_')
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
	return series_name, season, episode_number


def get_play_type(self, filepath):
	fname = os.path.basename(filepath)
	log(f"self.get_play_type running...", 'info')
	layout = []
	window_title = 'Select play type:'
	fname_line = [sg.Text(f"Setting info for:{fname}...")]
	play_type_combo = [sg.Combo(['series', 'movies', 'music'], 'series', enable_events=True,key='-PLAY_TYPE-')]
	layout.append(play_type_combo)
	layout.append(fname_line)
	win_key = window_title.lower().replace(' ', '_')
	win = sg.Window(window_title, layout, size=(650, 120), keep_on_top=False, element_justification='center', finalize=True)
	self.windows[win_key] = win
	data = None
	while True:
		event, values = win.read()
		if event == sg.WIN_CLOSED:
			del self.windows[win_key]
			break
		else:
			play_type = values[event]
			win.close()
	log(f"play_type:{play_type}", 'info')
	return play_type


def ssh(com):
	com = f"ssh monkey@192.168.1.2 \"{com}\""
	try:
		ret = subprocess.check_output(com, shell=True).decode().strip()
	except Exception as e:
		print(f"SSH command encountered an error:{e}")
		ret = []
	if "\n" in ret:
		ret = ret.splitlines()
	else:
		if ret != []:
			ret = [ret]
	if ret == ['']:
		ret = []
	return ret


def sqlite3(com):
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	com = f"sqlite3 \"{dbfile}\" \"{com}\""
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret == '':
		ret = None
	elif "\n" in ret:
		ret = ret.splitlines()
	return ret


def test_exists(filepath):
	for table in ['series', 'movies']:
		com = f"select id from {table} where filepath like '%{filepath}%';"
		ret = sqlite3(com)
		if ret is not None:
			return True, ret
	return False, None

def mv(from_path, to_path):
	com = f"cp \'{from_path}\' \'{to_path}\'"
	print("com:", com)
	log(f"Moving: {to_path}...", 'info')
	ret = ssh(com)
	if ret == []:
		return True
	else:
		print(ret[0])
		return False


def migrate(tid):
	from_path = None
	to_path = None
	try:
		download_dir = conf['pbdl']['download_dir']
	except Exception as e:
		download_dir = '/var/lib/transmission-daemon/downloads'
		log(f"Download directory not in conf! Adding...", 'info')
		conf['pbdl']['download_dir'] = download_dir
		writeConf(conf)
	files = get_files(tid)
	for fname in files:
		ret = []
		#target = f"{download_dir}/{torrents[tid]['name']}/{fname}"
		from_path = get_fullpath(fname)
		print("from_path:", from_path)
		ext = os.path.splitext(from_path)[1]
		play_type = test_media(from_path)
		if play_type == 'series':
			try:
				series_name, season, episode_number = test_media(os.path.basename(from_path), True)
				print(series_name, season, episode_number)
			except Exception as e:
				print("Couldn't parse series info from filepath. Getting from user...")
				series_name, season, episode_number = get_series_info(from_path)
			info = query_series(series_name=series_name, season=season, episode_number=episode_number)
			#to_path = os.path.join(conf['media_directories']['series'], series_name, f"S{season}", f"{series_name}.S{season}E{episode_number}.{info['episode_name']}{ext}")
			to_path = os.path.join('/var/storage/Series', series_name, f"S{season}", f"{series_name}.S{season}E{episode_number}.{info['episode_name']}{ext}")
			db_path = os.path.join(conf['media_directories']['series'], series_name, f"S{season}", f"{series_name}.S{season}E{episode_number}.{info['episode_name']}{ext}")
			to_dir = os.path.dirname(to_path)
			print("todir:", to_dir)
			print("from:", from_path)
			ssh(f"mkdir -p \'{to_dir}\'")
		elif play_type == 'movies':
			try:
				title, year = test_media(from_path, True)
			except Exception as e:
				print("Couldn't parse movie info from filepath. Getting from user...")
				title, year = get_movie_info(from_path)
			info = query_movies(title)
			#to_path = os.path.join(conf['media_directories']['movies'], f"{title} ({year})", f"{title} ({year}){ext}")
			to_path = os.path.join('/var/storage/Movies', f"{title} ({year})", f"{title} ({year}){ext}")
			db_path = os.path.join(conf['media_directories']['movies'], f"{title} ({year})", f"{title} ({year}){ext}")
			to_dir = os.path.dirname(to_path)
			ssh(f"mkdir -p \'{to_dir}\'")
		print("to path:", to_path)
		to_path = to_path.replace("'", '').replace('"', '')
		if not mv(from_path, to_path):
			break
		else:
			_id = None
			fname = os.path.basename(to_path)
			exists, _ids = test_exists(to_path)
			if exists:
				for item in _ids:
					log(f"File already exists with id {int(item)} ({to_path})", 'warning')	
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
						db_path = db_path.replace("'", "%27")
						vals.append(f"\'{db_path}\'")
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
			dbfile = os.path.join(DATA_DIR, 'nplayer.db')
			com = f"sqlite3 \"{dbfile}\" \"{qstring}\""
			ret = subprocess.check_output(com, shell=True).decode().strip()
			if ret:
				log(f"Error: Add to database failed for file '{to_path}': {ret}", 'error')
			else:
				log("Ok!")
	return True


if __name__ == "__main__":
	import sys
	try:
		tids = [int(sys.argv[1])]
	except:
		pbdl = pbdl()
		torrents = pbdl.get_torrents()
		tids = list(torrents.keys())
	for tid in tids:
		migrate(tid)
