import PySimpleGUI as sg
import pickle
import os
import subprocess
import pickle
import os
import requests
from np.core.nplayer_db import querydb
from np.core.log import np_logger
from np.core.conf import readConf, writeConf
from np.utils.xrandr import xrandr

log = np_logger().log_msg


def sqlite3(query):
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	com = f"sqlite3 \"{dbfile}\" \"{query}\""
	try:
		ret = subprocess.check_output(com, shell=True).decode().strip().replace('|', ':')
		if ret != '':
			if '::' in ret:
				ret = ret.replace('::', ':None:')
			if "\n" in ret:
				ret = ret.split("\n")
			return ret
		else:
			return None
	except Exception as e:
		#log(f"Error: sqlite3 command failed! {e}", 'error')
		return None


def get_local_ip():
	com = "ip -o -4 a s | awk -F'[ /]+' '$2!~/lo/{print $4}' | grep \"192.168\""
	return sg.subprocess.check_output(com, shell=True).decode().strip()

def shell(com, wait=False, cwd=None):
	if cwd == None:
		cwd = os.getcwd()
	com = f"cd \"{cwd}\"; {com}"
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret != '':
		return ret
	elif ret == '' or ret is None:
		return None

def check_process(pid):
	return sg.execute_subprocess_still_running(pid)


def python(filepath):
	ret = sg.execute_py_file(filepath)
	return ret

def get_res(filepath):
	try:
		com = f"ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 \"{filepath}\""
		w, h = subprocess.check_output(com, shell=True).decode().strip().split('x')
		out = (int(w), int(h))
		return out
	except Exception as e:
		log(f"Get res failed!:{e}", 'error')
		return None


def enable_debug():
	conf = readConf()
	conf['debug'] = True
	writeConf(conf)
	log("Debug enabled!", 'info')


def disable_debug():
	conf = readConf()
	conf['debug'] = False
	writeConf(conf)
	log("Debug disabled!", 'info') 


def read_history():
	history_file = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.series.history')
	if not os.path.exists(history_file):
		data_dir = os.path.join(os.path.expanduser("~"), ".np")
		ret = subprocess.check_output(f"cd \"{data_dir}\"; touch nplayer.log", shell=True).decode().strip()
		if ret != '':
			print("whoops!", ret)
	history_dict = {}
	try:
		with open (history_file, 'rb') as f:
			history_dict = pickle.load(f)
		f.close()			
	except Exception as e:
		log(f"Exception in core.py, read_history, line 223:{e}", 'error')
	return history_dict


def write_history(history_dict):
	history_file = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.series.history')
	try:
		with open (history_file, 'wb') as f:
			pickle.dump(history_dict, f)
		f.close()
		return True
	except Exception as e:
		log(f"Exception in core.py, write_history, line 234:{e}", 'error')
		return False


def set_play_type(play_type=None):
	conf = readConf()
	if play_type is not None:
		conf['play_type'] = play_type
		writeConf(conf)
		log('core.py, set_play_type: Conf file written!', 'info')
		return True
	else:
		log('core.py, set_play_type: No type provided!', 'error')
		return False


def get_scaling():
	# called before window created
	root = sg.tk.Tk()
	scaling = root.winfo_fpixels('1i')/72
	root.destroy()
	return scaling


def calculate_scale(_file, win_size=None, _type='file'):
	xdata = xrandr()
	conf = readConf()
	if win_size is not None:
		w, h = win_size
	else:
		screen = conf['screen']
		w, h = int(xdata[screen]['w']), int(xdata[screen]['h'])
	if _file == None:
		return 0
	log(f"ACTION:calculate_scale, file='{_file}', type='{type(_file)}'", 'info')
	if _type != 'file':
		log(f"type is not file, cannot calculate scale:{_type}", 'error')
		return False
	if not os.path.exists(_file):
		log(f"File not found:{_file}", 'error')
		return False
	try:
		vw, vh = get_res(_file)
	except Exception as e:
		log(f"Exception in core.py, calculate_scale:{e}", 'error')
		vw, vh = 1024, 768
	if vw is None or vh is None or h is None or w is None:
		return False
	if vw == 0 or vh == 0 or h == 0 or w == 0:
		return False
	if h >= vh and w >= vw:
		sw = h / vh
		sh = w / vw
	elif h <= vh and w <= vw:
		sw = vh / h
		sh = w / vw
	else:
		sw = 1.0
		sh = 1.0
	if sw <= sh:
		scale = float(sw)
	elif sw >= sh:
		scale = float(sh)
	else:
		scale = float(sw)
	return scale


def create_media(play_type=None, rows=None):
	playlist = []
	if play_type == None:
		try:
			conf = readConf()
			play_type = conf['play_type']
		except:
			play_type = 'series'
	if play_type == 'series' or play_type == 'videos':
		if rows == None:
			rows = querydb(table='series', column='id,series_name,tmdbid,season,episode_number,episode_name,description,air_date,still_path,filepath', query='isactive = 1')
		for _id, series_name, tmdbid, season, episode_number, episode_name, description, air_date, still_path, filepath in rows:
			if ':' in episode_name:
				chunks = episode_name.split(':')
				j = '|'
				episode_name = j.join(chunks)
			string = ("series:" + series_name + ":" + str(season) + ":" + str(episode_number) + ":" + episode_name + ":" + str(_id))
			playlist.append(string)
	if play_type == 'movies' or play_type == 'videos':
		rows = querydb(table='movies', column='id,tmdbid,title,year,release_date,description,poster,filepath', query='isactive = 1')
		for _id, tmdbid, title, year, release_date, description, poster, filepath in rows:
			string = ("movies:" + title + ":" + str(year) + ":" + str(_id))
			playlist.append(string)
	if play_type == 'music':
		rows = querydb(table = 'music', column='id,title,artist,album', query='isactive = 1')
		for _id, title, artist, album in rows:
			string = (f"music:{artist}:{title}:{album}:{_id}")
			playlist.append(string)
	return playlist


def get_version():
	path = os.path.join(os.path.expanduser("~"), '.np', 'version.txt')
	if os.path.exists(path):
		with open(path, "r") as f:
			version = f.read().strip()
		f.close()
	else:
		log(f"Unable to get current version info from file! (Not installed from repo?) Setting default '1.0'...", 'warning')
		version = 1.0
	return version


def match_repo_version():
	# returns False if local install doesn't match repo version, indicating update is needed.
	url = 'https://raw.githubusercontent.com/darthmonkey2004/python_np/master/version.txt'
	r = requests.get(url)
	if r.status_code == 200:
		repo_version = float(r.text)
	else:
		# if unable to get version, return no match
		log(f"Unable to retreive version from github: (Bad status code {r.status_code})!", 'error')
		return False
	version = float(get_version())
	if repo_version > version:
		log(f"A newer version of nplayer is available: {repo_version}. May wish to update...")
		return False
	elif repo_version < version:
		log(f"Git push needed, somehow changes failed to push (repo_version={repo_version}, local_version={version})", "warning")
		return False
	elif repo_version == version:
		log(f"Versions match! No action needed.", 'info')
		return True

def get_functions(pyfile):
	with open(pyfile, 'r') as f:
		data = f.read().split("\n")
	f.close()
	lines = []
	for line in data:
		if 'def ' in line:
			lines.append(line.split('def ')[1].split('(')[0])
	return lines



def change_series_name(old, new):
	ret = sqlite3(f"update series set series_name = \'{new}\' where series_name like \'{old}\';")
	if ret is not None:
		print("core.change_series_name():Error! {ret}", 'error')
		return False
	else:
		return True



def test_play_mode(playlist_object):
	if type(playlist_object) != list:
		l = playlist_object.playlist
	else:
		l = playlist_object
	print("type:", type(l))
	low = 0
	med = round(len(l) / 2)
	hi = len(l) - 1
	#true if databse, False if playlist
	if ':' in l[low]:
		t1 = True
	elif '/' in l[low] and '.' in l[low]:
		t1 = False
	if ':' in l[med]:
		t2 = True
	elif '/' in l[med] and '.' in l[med]:
		t2 = False
	if ':' in l[hi]:
		t3 = True
	elif '/' in l[hi] and '.' in l[hi]:
		t3 = False
	pos = 0
	if t3:
		pos += 1
	if t2:
		pos += 1
	if t1:
		pos += 1
	if pos >= 2:
		playlist_mode = 'database'
	else:
		playlist_mode = 'playlist'
	return playlist_mode
