import PySimpleGUI as sg
import sys, traceback
import subprocess
from np.core.log import np_logger
from np.core.conf import readConf, writeConf
from np.core.nplayer_db import get_columns
from np.utils.pbdl.se_isin import se_isin
from np.utils.pbdl.ty_isin import ty_isin
from np.core.core import shell
from np.utils.pbdl.rotten_tomatoes import get_episode_data, get_season_data, get_all_series_data, get_seasons, get_movie_data
from np.utils.pbdl.query_series import query_series
from np.utils.pbdl.query_movies import query_movies
import os
import pickle

log = np_logger().log_msg
conf = readConf()
DATA_DIR = os.path.join(os.path.expanduser("~"), '.np')
SFTP_DIR = os.path.join(DATA_DIR, 'sftp')
HOME = os.path.expanduser("~")


def set_empty(table='movies'):
	pragma = get_columns(table)
	columns = list(pragma.keys())
	info = {}
	for key in columns:
		dtype = pragma[key]['data_type']
		if dtype == 'INTEGER' or dtype == 'BOOL':
			info[key] = 0
		elif dtype == 'TEXT':
			info[key] = 'Unknown'
	return info


def send_command(com):
	return shell(com)


def mount_sftp():
	is_mounted = test_sftp_mount()
	if is_mounted == False:
		user = HOME.split('/home/')[1]
		#string = (f"{user}@{conf['pbdl_url']}")
		#media_dir  = ("/var/lib/transmission-daemon/downloads")
		#com = (f"sshfs \"{string}:{media_dir}\" \"{SFTP_DIR}\"")
	
		com = (f"sshfs \"{user}@{conf['pbdl_url']}:/var/lib/transmission-daemon/downloads\" \"{SFTP_DIR}\"")
		log(f"Com:{com}", 'info')
	
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error: Unable to mount sftp: {ret}", 'error')
			return False
		else:
			return True

def test_sftp_mount(mnt_point=None):
	if mnt_point == None:
		mnt_point = SFTP_DIR
	com = (f"mount -l | grep \"{mnt_point}\"")
	try:
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Mount test returned data: {ret}", 'info')
			return True
		else:
			log(f"Mount test failed! No data.", 'info')
			return False
	except:
		log(f"Mount test command failed! Not in mount list....", 'info')
		return False


def umount_sftp():
	is_mounted = test_sftp_mount()
	if is_mounted is True:
		com = f"fusermount -u \"{SFTP_DIR}\""
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error: Unable to unmount sftp: {ret}", 'error')
			return False
		else:
			return True	


def get_fullpath(query, t=None):
	play_type = test_media(query)
	found = None
	if t == None:
		from_dir = SFTP_DIR
	elif t == 'local':
		from_dir = '/var/lib/transmission-daemon/downloads'
	to_dir = conf['media_directories'][play_type]
	com = (f"find \"{from_dir}\" -type f")
	found = subprocess.check_output(com, shell=True).decode().strip().split("\n")	
	for item in found:
		if query in item:
			found = item
			return found
	if found is None:
		log(f"Unable to find full path for \"{query}\"", 'warning')
		return None

def refresh_info(torrents, tid):
	files = get_files(tid)
	for filepath in files:
		torrents[tid]['files'] = {}
		torrents[tid]['files'][filepath] = {}
		play_type = test_media(filepath)
		columns = list(get_columns(play_type).keys())
		info = set_empty(play_type)
		torrents[tid]['files'][filepath]['info'] = info
		torrents[tid]['files'][filepath]['info']['play_type'] = play_type
		if play_type == 'series':
			series_name, season, episode_number = test_media(filepath, True)
			info = set_empty('series')
			info['series_name'] = series_name
			info['season'] = season
			info['episode_number'] = episode_number
		elif play_type == 'movies':
			title, year = test_media(filepath, True)
			info = set_empty('movies')
			info['title'] = title
			info['year'] = year
		lookup_type = '-rotten tomatoes-'
		torrents[tid]['files'][filepath]['info']['lookup_type'] = lookup_type
		ret = lookup(torrents[tid]['files'][filepath]['info'])
		try:
			if ret['results'] == True:
				torrents[tid]['files'][filepath]['info'] = ret
			return torrents[tid]
		except Exception as e:
			log(f"Error: Unable to automatically complete missing data for id {tid}! ({e}). Skipping...", 'error')
			return None


def add_to_db(torrents):
	for tid in list(torrents.keys()):
		try:
			hasfiles = torrents[tid]['files']
		except:
			info = refresh_info(torrents, tid)
			if info is None:
				break
		for filepath in list(torrents[tid]['files'].keys()):
			info = torrents[tid]['files'][filepath]['info']
			fname = os.path.basename(filepath).replace("'", "%27")
			try:
				play_type = info['play_type']
			except:
				play_type = test_media(filepath)
			exists = None
			dbfile = os.path.join(DATA_DIR, 'nplayer.db')
			com = f"sqlite3 \"{dbfile}\" \"select id from {play_type} where filepath like \'%{fname}%\';\""
			exists = subprocess.check_output(com, shell=True).decode().strip()
			if exists is not None and exists != '':
				log(f"File already exists with id {exists} ({filepath}). Aborting...", 'warning')
				break
			fullpath = None
			is_mounted = test_sftp_mount()
			if is_mounted is False:
				mount_sftp()		
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
						fullpath = get_fullpath(filepath)
						fullpath = fullpath.replace("'", "%27")
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
			dbfile = os.path.join(DATA_DIR, 'nplayer.db')
			com = f"sqlite3 \"{dbfile}\" \"{qstring}\""
			ret = subprocess.check_output(com, shell=True).decode().strip()
			if ret:
				log(f"Error: Add to database failed for file '{filepath}': {ret}", 'error')
			else:
				log("Ok!")


def migrate_series():
	conf = readConf()
	media_dir = conf['media_directories']['series']
	db = os.path.join(DATA_DIR, 'nplayer.db')
	com = (f"sqlite3 {db} \"select id,series_name,season,episode_number,episode_name,filepath from series where filepath like \'%{SFTP_DIR}%\';\"")
	results = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	for item in results:
		if item == '':
			return None
		_id, series_name, season, episode_number, episode_name, filepath = item.split('|')
		if '%27' in filepath:
			filepath = filepath.replace("%27", "'")
		l = len(filepath) - 4
		ext = filepath[l:]
		newdir = (f"{media_dir}/{series_name}/S{season}")
		com = (f"mkdir -p \"{newdir}\"")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error creating directory: {newdir}. ({ret})", 'error')
			break
		newpath = (f"{newdir}/{series_name}.S{season}E{episode_number}.{episode_name}{ext}").replace("'", "")
		log(f"Migrating file '{filepath}' to '{newpath}'..", 'info')
		com = (f"cp \"{filepath}\" \"{newpath}\"")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error migrating file: {filepath} to {newpath}. ({ret})", 'error')
			break
		else:
			log(f"File moved!", 'info')
		com = (f"sqlite3 {db} \"update series set filepath = \'{newpath}\' where id = {_id};\"")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error renaming file in database: id={_id}", 'error')
			break


def migrate_movies():
	conf = readConf()
	media_dir = conf['media_directories']['movies']
	db = os.path.join(DATA_DIR, 'nplayer.db')
	com = (f"sqlite3 {db} \"select id,title,year,filepath from movies where filepath like \'%{SFTP_DIR}%\';\"")
	results = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	for item in results:
		try:
			_id, title, year, filepath = item.split('|')
		except Exception as e:
			log(f"Unable to get info from movie: {e}. Data={item}")
			input("Press enter to continue")
			return
		if '%27' in filepath:
			filepath = filepath.replace("%27", "'")
		l = len(filepath) - 4
		ext = filepath[l:]
		newdir = os.path.join(media_dir, f"{title} ({year})")
		com = (f"mkdir -p \"{newdir}\"")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error creating directory: {newdir}. ({ret})", 'error')
			break
		newpath = os.path.join(newdir, f"{title} ({year}){ext}").replace("'", "")
		log(f"Migrating file '{filepath}' to '{newpath}'..", 'info')
		com = (f"cp \"{filepath}\" \"{newpath}\"")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error migrating file: {filepath} to {newpath}. ({ret})", 'error')
			break
		else:
			log(f"File moved!", 'info')
		com = (f"sqlite3 {db} \"update movies set filepath = \'{newpath}\' where id = {_id};\"")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error renaming file in database: id={_id}", 'error')
			break

def get_torrents_old():
	torrents = {}
	com = (f"transmission-remote {conf['pbdl_url']} -l")
	data = subprocess.check_output(com, shell=True).decode().strip().split('\n')
	outlist = []
	pos = -1
	tid = None
	for line in data:
		pos += 1
		outstr = None
		if 'n/a' in line and 'None' in line:
			log(f"Torrent skipped: (no data)", 'info')
		if pos > 0 and 'Sum:' not in line and 'ID' not in line and 'n/a' not in line and 'None' not in line:
			chunks = line.split(' ')
			cpos = -1
			for chunk in chunks:
				if chunk != '':
					cpos += 1
					if cpos == 0:
						tid = int(chunk)
						torrents[tid] = {}
						torrents[tid]['files'] = get_files(tid)
						torrents[tid]['tid'] = tid
					elif cpos == 1:
						torrents[tid]['percent'] = chunk
					elif cpos == 2:
						torrents[tid]['have'] = chunk
					elif cpos == 3:
						torrents[tid]['size_unit'] = chunk
					elif cpos == 4:
						torrents[tid]['eta'] = chunk
					elif cpos == 5:
						torrents[tid]['upload_rate'] = chunk
					elif cpos == 6:
						torrents[tid]['download_rate'] = chunk
					elif cpos == 7:
						torrents[tid]['ratio'] = chunk
					elif cpos == 8:
						torrents[tid]['status'] = chunk
						name = line.split(torrents[tid]['status'])[1].strip()
						torrents[tid]['name'] = name
			
	return torrents

def get_torrents():
	com = "transmission-remote -l | grep -v \"ID\" | grep -v \"Sum\""
	try:
		lines = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	except:
		return {}
	torrents = {}
	for line in lines:
		tid = int(line.strip().split(' ')[0])
		torrents[tid] = {}
		if 'n/a' in line:
			torrents[tid]['percent'] = 0
			s = 'n/a'
		else:
			torrents[tid]['percent'] = line.split(f"{tid} ")[1].split('%')[0].strip()
			s = f"{torrents[tid]['percent']}%"
		torrents[tid]['have'] = line.split(s)[1].strip().split('B ')[0].split(' ')[0]
		if torrents[tid]['percent'] == 0:
			size_unit = 'M'
		else:
			size_unit = line.split(s)[1].strip().split('B ')[0].split(' ')[1]
		torrents[tid]['size_unit'] = f"{size_unit}B"
		try:
			torrents[tid]['eta'] = line.split(f"{torrents[tid]['size_unit']}")[1].strip().split(' ')[0]
		except:
			torrents[tid]['eta'] = 'Unknown'
		if 'Finished' in line:
			status = 'Finished'
		elif 'Stopped' in line:
			status = 'Stopped'
		elif 'Downloading' in line:
			status = 'Downloading'
		torrents[tid]['status'] = status
		torrents[tid]['name'] = line.split(status)[1].strip()
		com = f"transmission-remote -t{tid} -f | grep -v \"Done\" | grep -v \"files):\""
		try:
			file_lines = subprocess.check_output(com, shell=True).decode().strip().split("\n")
			torrents[tid]['files'] = []
			for fline in file_lines:
				if 'MB' in fline:
					s = 'MB'
				elif 'KB' in fline:
					s = 'KB'
				elif 'GB' in fline:
					s = 'GB'
				elif 'TB' in fline:
					s = 'TB'
				torrents[tid]['files'].append(fline.split(s)[1].strip())
		except:
			torrents[tid]['files'] = []
	return torrents

def get_files(tid):
	com = (f"transmission-remote {conf['pbdl']['remote_ip']} -t{tid} -f | grep -v \'files):\' | grep -v \'#\' | grep -v \".jpg\" | grep -v \"sample\" | grep -v \".srt\" | grep -v \".nfo\" | grep -v \".txt\" | cut -d \"{os.path.sep}\" -f 2")
	try:
		data = send_command(com).split("\n")
	except:
		return []
	files = []
	for filepath in data:
		if filepath != '':
			if '%' in filepath:
				chunks = filepath.split(' ')
				cpos = -1
				for chunk in chunks:
					if chunk != '':
						cpos += 1
						if cpos == 5:
							filepath = filepath.split(chunk)[1]
						
						
			filepath = filepath.strip()
			files.append(filepath)
	try:
		pbdl_win['-TORRENT_FILES-'].update(files)
	except:
		pass
	return files


def test_media_type(filepath):
	is_series = se_isin(filepath)
	is_movie = ty_isin(filepath)
	if is_series is True:
		return 'series'
	elif is_movie is True:
		return 'movies'
	else:
		log(f"Error: Unknown type, couldn't parse keys from filepath! File: {filepath}", 'error')
		return False


def test_media(filepath, return_data=False):
	play_type = test_media_type(filepath)
	if return_data == False:
		return play_type
	elif return_data == True:
		if play_type == 'series':
			return parse_series(filepath)
		elif play_type == 'movies':
			return parse_movies(filepath)


def parse_series(filepath):
	conf = readConf()
	media_dir = conf['media_directories']['main']
	if media_dir in filepath:
		try:
			n = filepath.split(media_dir)[1].split(f"{os.path.sep}Series{os.path.sep}")[1].split(os.path.sep)[0]
			s = filepath.split(media_dir)[1].split(f"{os.path.sep}Series{os.path.sep}")[1].split(os.path.sep)[1].split('S')[1]
			e = filepath.split(media_dir)[1].split(f"{os.path.sep}Series{os.path.sep}")[1].split(os.path.sep)[2].replace('.', ' ').split(f"S{s}E")[1].split(' ')[0]
			return [n, s, e]
		except Exception as e:
			log(f"Error: Unknown issue! Structured filesystem wasn't parseable: {e}", 'error')
			return None, None, None
	else:
		sinfo = None
		season = None
		episode_number = None
		season, episode_number, sinfo = se_isin(filepath, True)
		play_type = 'series'
		length = len(filepath.split(sinfo)) - 1
		series_name = filepath.split(sinfo)[0].replace('.', ' ').strip()
		if os.path.sep in series_name:
			series_name = series_name.split(os.path.sep)[1]
		return [series_name, season, episode_number]
	
	
def parse_movies(filepath):
	title = None
	year = None
	if '(' in filepath and ')' in filepath:
		year = int(filepath.split('(')[1].split(')')[0])
		if year >= 1900:
			string = f" ({year}) "
			if string in filepath:
				title = filepath.split(string)[0].strip()
			else:
				string = ('(' + str(year) + ')')
				title = filepath.split(string)[0].strip()
		else:
			year = None
	else:
		title, year = ty_isin(filepath, True)
		
	return [title, year]


def lookup(args):
	play_type = args['play_type']
	lookup_type = args['lookup_type']
	if play_type == 'series':
		if lookup_type == '-rotten tomatoes-':
			data = get_episode_data(args['series_name'], args['season'], args['episode_number'])
			if data['results'] == True:
				log("Lookup successful!", 'info')
				return data
		elif lookup_type == '-TMDB-':
			data = query_series(args['series_name'], args['season'], args['episode_number'])
			if data['results'] == True:
				log("Lookup successful!", 'info')
				return data
	elif play_type == 'movies':
		if lookup_type == '-rotten tomatoes-':
			data = get_movie_data(args['title'])
			if data['results'] == True:
				log("Lookup successful!", 'info')
				return data
		elif lookup_type == '-TMDB-':
			data = query_movies(args['title'])
			if data['results'] == True:
				log("Lookup successful!", 'info')
				return data


def verify_series_name(series_name):
	db = os.path.join(DATA_DIR, 'nplayer.db')
	com = (f"sqlite3 \"{db}\" \"select distinct series_name from series where upper(series_name) like upper('%{series_name}%');\"")
	series_exists = None
	series_exists = subprocess.check_output(com, shell=True).decode().strip()
	if series_exists is None or series_exists == '':
		#test for year in name
		hasyear = ty_isin(series_name)
		if hasyear:
			#retest if year in series_name (like 'Archer 2009')
			series_name, _ = ty_isin(series_name, True)
			db = os.path.join(DATA_DIR, 'nplayer.db')
			com = (f"sqlite3 \"{db}\" \"select distinct series_name from series where upper(series_name) like upper('%{series_name}%');\"")
			series_exists = subprocess.check_output(com, shell=True).decode().strip()
			if series_exists is not None and series_exists != '':
				return series_exists
	if series_exists == '':
		series_exists = None
	return series_exists

def get_user_input(window_title='User Input', txt=None):
	user_input = None
	input_box = sg.Input(default_text='', enable_events=True, change_submits=True, do_not_clear=True, key='-USER_INPUT-', expand_x=True)
	input_btn = sg.Button(button_text='Ok', auto_size_button=True, pad=(1, 1), key='-OK-')
	if txt is not None:
		input_txt = sg.Text(txt)
		layout = [[input_box], [input_txt], [input_btn]]
	else:
		layout = [[input_box], [input_btn]]
	input_window = sg.Window(window_title, layout, keep_on_top=False, element_justification='center', finalize=True)
	while True:
		event, values = input_window.read()
		if event == sg.WIN_CLOSED:
			break
		elif event == '-OK-':
			input_window.close()
		elif event == '-USER_INPUT-':
			user_input = values[event]
	return user_input

def get_user_yn(window_title='Yes/No'):
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
		user_input = user_input
		break
	return user_input

def set_api_key_rt():
	conf = readConf()
	api_key = get_user_input("Rotten Tomatoes Api Key:", "You know you don't actually need a rotten tomatoes api key.. (wasting your time):")
	try:
		haskeys = conf['api_keys']
	except:
		conf['api_keys'] = {}
		log(f"Api keys not found in conf! Adding...", 'warning')
	conf['api_keys']['rotten_tomatoes'] = api_key
	writeConf(conf)
	log(f"Updated Rotten Tomatoes API Key: {api_key}", 'info')
	return api_key

def set_api_key_tmdb():
	conf = readConf()
	api_key = get_user_input("Enter TMDB api key:")
	try:
		haskeys = conf['api_keys']
	except:
		conf['api_keys'] = {}
		log(f"Api keys not found in conf! Adding...", 'warning')
	conf['api_keys']['TMDB'] = api_key
	writeConf(conf)
	log(f"Updated TMDB API Key: {api_key}", 'info')
	return api_key


def clear_data():
	savefile = os.path.join(DATA_DIR, 'pbdl.dat')
	if os.path.exists(savefile):
		com = f"rm \"{savefile}\""
		ret = shell(com)
		if ret:
			log(f"Error: Unable to remove savefile! Results:{ret}", 'error')
			return False
		torrents = get_torrents()
		ret = save_data(torrents)
		if ret is not True:
			log(f"Error: Unable to save current data! Details:{ret}", 'error')
	torrents = build_data(rebuild=True)
	return torrents

def save_data(torrents):
	log(f"Saving current data!", 'info')
	savefile = os.path.join(DATA_DIR, 'pbdl.dat')
	try:
		with open(savefile, "wb") as f:
			pickle.dump(torrents, f)
		f.close()
		if conf['debug'] == True:
			log(f"Torrent log updated.", 'info')
		return True
	except Exception as e:
		log(f"Error: Unable to write torrent log {e}: data: {torrents}", 'error')
		return False

def load_saved_data():
	#returns all previously saved data. Does not check to ensure more torrents added, use with resume only.
	savefile = os.path.join(DATA_DIR, 'pbdl.dat')
	if os.path.exists(savefile):
		bakdata = {}
		log("Restoring backup...")
		if os.path.exists(savefile):
			with open(savefile, "rb") as f:
				bakdata = pickle.load(f)
			f.close()
		log("Backup restored!", 'info')
		return bakdata
	else:
		log(f"Couldn't restore data: Save file not found!", 'warning')
		return None

def merge_saved_data():
	#returns all previously saved data, overwriting only if torrent id doesn't exist in current data
	torrents = get_torrents()
	#torrents = build_data()
	old = load_saved_data()
	if old is not None:
		#log(f"Saved data found! Merging...", 'info')
		for tid in torrents:
			if tid in old:
				torrents[tid]['files'] = old[tid]['files']
			elif tid not in old:
				pass
	else:
		log(f"No saved data found! Skipping merge..", 'info')
	return torrents


def build_data(rebuild=False, lookup_type=None):
	
	if lookup_type == None:
		lookup_type = '-rotten tomatoes-'
	try:
		if rebuild is False:
			log(f"Loading saved data...", 'info')
			torrents = load_saved_data()
			if torrents is not None:
				return torrents
			else:
				torrents = get_torrents()
		elif rebuild is True:
			torrents = get_torrents()
	except Exception as e:
		log(f"Unable to load saved data: {e}. Rebuilding...", 'warning')
	for tid in torrents.keys():
		files = get_files(tid)
		torrents[tid]['files']  = {}
		for filepath in files:
			play_type = test_media(filepath)
			try:
				results = torrents[tid]['files'][filepath]['info']['results']
			except Exception as e:
				log(f"Results tag not found: {e}", 'warning')
				results = None
			if results is None:
				torrents[tid]['files'][filepath] = {}
				torrents[tid]['files'][filepath]['info'] = set_empty(play_type)
				torrents[tid]['files'][filepath]['info']['play_type'] = play_type
				if torrents[tid]['files'][filepath]['info']['play_type'] == 'series':
					series_name, season, episode_number = test_media(filepath, True)
					tname = verify_series_name(series_name)
					if tname is not None:
						series_name = tname
					torrents[tid]['files'][filepath]['info']['series_name'] = series_name
					torrents[tid]['files'][filepath]['info']['season'] = season
					torrents[tid]['files'][filepath]['info']['episode_number'] = episode_number
					torrents[tid]['files'][filepath]['info']['lookup_type'] = lookup_type
				elif torrents[tid]['files'][filepath]['info']['play_type'] == 'movies':
					title, year = test_media(filepath, True)
					torrents[tid]['files'][filepath]['info']['title'] = title
					torrents[tid]['files'][filepath]['info']['year'] = year
					torrents[tid]['files'][filepath]['info']['lookup_type'] = lookup_type
				ret = lookup(torrents[tid]['files'][filepath]['info'])
				try:
					if ret['results'] == True:
						torrents[tid]['files'][filepath]['info'] = ret
				except Exception as e:
					log(f"Unable to get info for filepath {filepath}: {e}", 'warning')
	save_data(torrents)
	return torrents


if __name__ == "__main__":
	data = build_torrents()
	log(data, 'info')
	
