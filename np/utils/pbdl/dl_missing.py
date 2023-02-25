import pickle
import subprocess
from np.core.conf import readConf
from np.utils.pbdl.utils import sqlite3, shell, test_media
from np.utils.pbdl.search import *
from np.utils.pbdl.query_series import *
from np.core.nplayer_db import get_columns

conf = readConf()
media_dir = conf['media_directories']['series']
DATA_DIR = conf['DATA_DIR']

def ssh(com):
	remote_ip = conf['pbdl']['remote_ip']
	user = os.getlogin()
	com = f"ssh {user}@{remote_ip} \"{com}\""
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if "\n" in ret:
		ret = ret.splitlines()
	elif ret == '':
		ret = None
	return ret



def get_db_data():
	series = sqlite3("select distinct series_name from series;")
	db_data = {}
	for series_name in series:
		db_data[series_name] = {}
		tmdbid = get_series_id(series_name)
		db_data[series_name]['tmdbid'] = tmdbid
		seasons = sqlite3(f"select distinct season from series where series_name like '%{series_name}%';")
		db_data[series_name]['seasons'] = {}
		for season in seasons:
			season = int(season)
			db_data[series_name]['seasons'][season] = {}
			episodes = sqlite3(f"select id, episode_number from series where series_name like '%{series_name}%' and season = {season};")
			db_data[series_name]['seasons'][season]['episodes'] = {}
			for line in episodes:
				_id, episode_number = line.split('|')
				episode_number = int(episode_number)
				db_data[series_name]['seasons'][season]['episodes'][episode_number] = {}
				db_data[series_name]['seasons'][season]['episodes'][episode_number]['id'] = _id
				db_data[series_name]['seasons'][season]['episodes'][episode_number]['series_name'] = series_name
				db_data[series_name]['seasons'][season]['episodes'][episode_number]['season'] = season
				db_data[series_name]['seasons'][season]['episodes'][episode_number]['episode_number'] = episode_number
				db_data[series_name]['seasons'][season]['episodes'][episode_number]['tmdbid'] = tmdbid
	return db_data


def download(data=None, auto=True):
	t = torrent_mgr()
	if data is None:
		data = load_downloads()
	for line in data:
		magnets = line['magnet_data']
		if auto:
			magnet = magnets.values()[0]
		else:
			if len(magnets) == 1:
				magnet = magnets.values()[0]
			else:
				pos = 0
				for name in magnets.keys():
					pos += 1
					print(f"{pos}: {name}")
				pick = int(input("Enter choice: "))
				magnet = list(magnets.values())[pick]
		try:
			t.add(magnet)
		except Exception as e:
			print(f"Couldn't add magnet! {e}, data:{line}")
			return False
	return True

def get_missing():
	db_data = get_db_data()
	series = sqlite3("select distinct series_name from series;")
	missing = []
	for series_name in series:
		tmdbid = get_series_id(series_name)
		seasons = list(get_seasons(tmdbid).keys())
		for season in seasons:
			season = int(season)
			data = get_season_data(tmdbid, season)
			episodes = list(data['episodes'].keys())
			for episode_number in episodes:
				episode_number = int(episode_number)
				episode_name = data['episodes'][episode_number]['episode_name']
				try:
					d = db_data[series_name]['seasons'][season]['episodes'][episode_number]
				except:
					string = f"{series_name}|{tmdbid}|{season}|{episode_number}|{episode_name}"
					print("Added missing:", string)
					missing.append(string)
	return db_data, missing


def add(info, play_type='series'):
	filepath = info['filepath']
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
				fullpath = filepath
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
					print(f"Exception {e}: Column:{column}", 'error')
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
		print(f"Error: Add to database failed for file '{filepath}': {ret}", 'error')
	else:
		print("Ok!")



def filter_missing():
	db_data, missing = get_missing()
	filtered = []
	add_to_db = []
	for line in missing:
		series_name, tmdbid, season, episode_number, episode_name = line.split('|')
		path = os.path.join(media_dir, series_name, f"S{season}")
		if os.path.exists(path):
			tag = f"*.S{season}E{episode_number}.*"
			com = f"find \"{path}\" -name \"{tag}\""
			ret = shell(com)
			if ret is None:
				print("Added missing (no S/E tag found):", line)
				filtered.append(line)
			else:
				print(f"Missing from database:{line}")
				add_to_db.append(f"{line}|{ret}")
		else:
			print("No season directory, legit missing:", line)
			filtered.append(line)
	return filtered, add_to_db



def add_missing(add_to_db=None):
	keys = ['series_name', 'tmdbid', 'season', 'episode_number', 'episode_name', 'description', 'air_date', 'still_path']
	if add_to_db is None:
		_, add_to_db = filter_missing()
	for line in add_to_db:
		series_name, tmdbid, season, episode_number, episode_name, filepath = line.split('|')
		info = get_episode_data(_id=series_name, season=season, episode_number=episode_number)
		info['filepath'] = filepath
		add(info)
		input()

def get_download_uris(series_name, season=None, episode_number=None):
	query = None
	if season is None and episode_number is None:
		query = series_name
	elif season is not None and episode_number is None:
		query = f"{series_name} season {season}"
	elif season is not None and episode_number is not None:
		if len(str(season)) == 1:
			season = f"0{season}"
		if len(str(episode_number)) == 1:
			episode_number = f"0{episode_number}"
		query = f"{series_name} S{season}E{episode_number}"
	print(query)
	if query is not None:
		return search(query)
	else:
		return {}


def get_dict(missing=None):
	if missing is None:
		missing, add_to_db = filter_missing()
	dl_data = []
	for line in missing:
		d = {}
		series_name, tmdbid, season, episode_number, episode_name = line.split("|")
		d['series_name'] = series_name
		d['tmdbid'] = tmdbid
		d['season'] = season
		d['episode_number'] = episode_number
		d['episode_name'] = episode_name
		d['magnet_data'] = None
		dl_data.append(d)
	return dl_data


def get_downloads(data=None):
	if data is None:
		data = get_dict()
	dl_data = []
	for line in data:
		d = {}
		series_name = line['series_name']
		tmdbid = line['tmdbid']
		season = line['season']
		episode_number = line['episode_number']
		episode_name = line['episode_name']
		d['series_name'] = series_name
		d['tmdbid'] = tmdbid
		d['season'] = season
		d['episode_number'] = episode_number
		d['episode_name'] = episode_name
		ret = get_download_uris(series_name=series_name, season=season, episode_number=episode_number)
		if ret == {}:
			ret = get_download_uris(series_name=series_name, season=season)
			if ret == {}:
				ret = get_download_uris(series_name=series_name)
				if ret == {}:
					print("Found nothing (?) for:", line)
					input()
		if ret == {}:
			ret = None
		d['magnet_data'] = ret
		dl_data.append(d)
	return dl_data

def save_downloads(dl_data=None, datfile=None):
	if dl_data is None:
		dl_data = get_dict()
	if datfile is None:
		datfile = os.path.join(os.path.expanduser("~"), '.np', 'downloads.dat')
	with open(datfile, 'wb') as f:
		pickle.dump(dl_data, f)
		f.close()

def load_downloads(datfile=None):
	if datfile is None:
		datfile = os.path.join(os.path.expanduser("~"), '.np', 'downloads.dat')
	with open(datfile, 'rb') as f:
		dl_data = pickle.load(f)
		f.close()
	return dl_data

if __name__ == "__main__":
	t = torrent_mgr()
	if not t.vpn_status():
		t.start_vpn()
	dl_data = load_downloads()
