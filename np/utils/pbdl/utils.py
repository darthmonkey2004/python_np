import re
from np.utils.id3 import tag
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
import json
import requests
from urllib.parse import quote, unquote
id3 = tag()
log = np_logger().log_msg
conf = readConf()
DATA_DIR = os.path.join(os.path.expanduser("~"), '.np')
SFTP_DIR = os.path.join(DATA_DIR, 'sftp')
HOME = os.path.expanduser("~")
media_dir = conf['media_directories']['movies']
db = os.path.join(DATA_DIR, 'nplayer.db')

def get_public_ip():
	url = 'https://www.showmyip.com/'
	r = requests.get(url)
	data = r.text.split("\n")
	for line in data:
		if 'Your IPv4' in line:
			return line.split('<b>')[1].split('</b>')[0]

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
	
		com = (f"sshfs \"{user}@{conf['pbdl_url']['remote_ip']}:/var/lib/transmission-daemon/downloads\" \"{SFTP_DIR}\"")
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
			if '.srt' not in item and '.png' not in item and '.jpg' not in item and '.part' not in item:
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
			info['air_date'] = '11-11-1111'
		elif play_type == 'movies':
			title, year = test_media(filepath, True)
			info = set_empty('movies')
			info['title'] = title
			info['year'] = year
		lookup_type = '-TMDB-'
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
	dbfile = os.path.join(DATA_DIR, 'nplayer.db')
	tids = []
	for tid in list(torrents.keys()):
		percent = torrents[tid]['percent']
		if percent == '100%':
			tids.append(tid)
	for tid in tids:
		try:
			hasfiles = torrents[tid]['files']
		except:
			torrents[tid]['files'] = get_files(tid)
			if torrents[tid]['files'] is None:
				break
		for filepath in list(torrents[tid]['files'].keys()):
			lookup = False
			log(f"add_to_db:filepath={filepath}", 'info')
			play_type = test_media(filepath)
			if play_type == 'movies':
				title, year = test_media(filepath, True)
				torrents[tid]['files'][filepath]['info'] = query_movies(title)
				torrents[tid]['files'][filepath]['info']['title'] = title
				torrents[tid]['files'][filepath]['info']['year'] = year
			elif play_type == 'series':
				series_name, season, episode_number = test_media(filepath, True)
				series_name = series_name.title()
				torrents[tid]['files'][filepath]['info'] = query_series(series_name, season, episode_number)
				torrents[tid]['files'][filepath]['info']['series_name'] = test_series_name(series_name)
				torrents[tid]['files'][filepath]['info']['season'] = int(season)
				torrents[tid]['files'][filepath]['info']['episode_number'] = int(episode_number)
			info = torrents[tid]['files'][filepath]['info']
			torrents[tid]['files'][filepath]['info']['play_type'] = play_type
			_id = None
			fname = os.path.basename(filepath)
			exists, _id = test_exists(filepath)
			if exists:
				_id = _id.split("\n")
				for item in _id:
					log(f"File already exists with id {int(item)} ({filepath}). Removing stale db entries...", 'warning')
					com = f"sqlite3 \"{dbfile}\" \"delete from {play_type} where id = {int(item)};\""
					ret = subprocess.check_output(com, shell=True).decode().strip()
					if ret == '':
						log(f"pbdl.utils.add_to_db:Removed from db: '{filepath}'", 'info')
					else:
						log(f"Failed to remove item {ret}", 'warning')
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
	return True


def test_exists(filepath, play_type=None):
	if play_type is None:
		play_type = test_media(filepath)
	fname = os.path.basename(filepath)
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	com = f"sqlite3 \"{dbfile}\" \"select id from {play_type} where filepath like \'%{fname}%\';\""
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret != '':
		return True, ret
	else:
		return False, None
	


def migrate(torrents=None):
	log(f"Migrating series files...", 'info')
	conf = readConf()
	media_dir = conf['media_directories']['movies']
	db = os.path.join(DATA_DIR, 'nplayer.db')
	com = f"sqlite3 {db} \"select id,title,year,filepath from movies where filepath like \'%transmission-daemon/downloads%\';\""
	print(f"migrate:Movies - command=\'{com}\'", 'info')
	items = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	com = f"sqlite3 {db} \"select id,series_name,season,episode_number,episode_name,filepath from series where filepath like \'%transmission-daemon/downloads%\';\""
	items += subprocess.check_output(com, shell=True).decode().strip().split("\n")
	print(f"migrate:Series - command=\'{com}\'", 'info')
	movies = []
	series = []
	for item in items:
		if item is not None and item != '':
			log(f"Getting play type for item:{item}", 'info')
			play_type = get_play_type(item)
			if  play_type  == 'series':
				series.append(item)
				log(f"utils.migrate():Series item added - {item}!", 'info')
			elif play_type == 'movies':
				movies.append(item)
				log(f"utils.migrate():Movie item added - {item}!", 'info')
		else:
			log(f"utils.migrate():Item was empty! item={item}", 'error')
	ret = migrate_series(series)
	if ret:
		log("Series migration finished!", 'info')
	else:
		log("Series migration failed!", 'error')
	log(f"Migrating movie files...", 'info')
	ret = migrate_movies(movies)
	log(f"pbdl.utils.migrate_movies:movies({len(movies)})={movies}", 'info')
	if movies is None or len(movies) == 0 or movies == ['']:
		log(f"No results for movies!", 'info')
		return
	if ret:
		log("Movies migration finished!", 'info')
	else:
		log("Movies migration failed!", 'error')
	log(f"Finished!", 'info')
	


def migrate_series(results):
	conf = readConf()
	pos = 0
	ct = len(results)
	for item in results:
		pos += 1
		if item == '':
			log(f"No series in database in sftp directory! (results={results})", 'warning')
			return False
		#_id, series_name, season, episode_number, episode_name, filepath = item.split('|')
		series_name = item['series_name']
		season = item['season']
		episode_number = item['episode_number']
		episode_name = item['episode_name']
		filepath = item['filepath']
		if '%27' in filepath:
			filepath = filepath.replace("%27", "'")
		ext = os.path.splitext(filepath)[1]
		newdir = (f"{media_dir}/{series_name}/S{season}")
		com = (f"mkdir -p \"{newdir}\"")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error creating directory: {newdir}. ({ret})", 'error')
			return False
		newpath = (f"{newdir}/{series_name}.S{season}E{episode_number}.{episode_name}{ext}").replace("'", "")
		log(f"Migrating file '{filepath}' to '{newpath}'..", 'info')
		com = (f"cp \"{filepath}\" \"{newpath}\"")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error migrating file: {filepath} to {newpath}. ({ret})", 'error')
			return False
		else:
			log(f"File moved!", 'info')
		if not os.path.exists(filepath):
			log(f"migrate_movies:ERROR!File not found!", 'error')
			return False
		com = (f"sqlite3 {db} \"update series set filepath = \'{newpath}\' where id = {_id};\"")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error renaming file in database: id={_id}", 'error')
			return False
		log(f"migrate_movies:Done with {pos} of {ct}..", 'info')


def migrate_movies(results):
	conf = readConf()
	pos = 0
	ct = len(results)
	for item in results:
		pos += 1
		log(f"Migrating {pos} of {ct}...({item})", 'info')
		try:
			_id, title, year, filepath = item.split('|')
			if title == 'Unknown' or year == 'Unknown':
				title, year = test_media(filepath, True)
		except Exception as e:
			log(f"Unable to get info from movie: {e}. Data={item}")
			return
		if '%27' in filepath:
			filepath = filepath.replace("%27", "'")
		ext = os.path.splitext(filepath)[1]
		newdir = os.path.join(media_dir, f"{title} ({year})")
		com = (f"mkdir -p \"{newdir}\"")
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if ret:
			log(f"Error creating directory: {newdir}. ({ret})", 'error')
			return False
		newpath = os.path.join(newdir, f"{title} ({year}){ext}").replace("'", "")
		if not os.path.exists(filepath):
			log(f"File doesn't exist ({filepath})! Removing from db...", 'warning')
			com = f"sqlite3 {db} \"delete from movies where filepath = \'{filepath}\';\""
			ret = subprocess.check_output(com, shell=True).decode().strip()
			if ret:
				log(f"pbdl.utils.migrate_movies:Removed from db: '{filepath}'", 'info')
				return False
		else:
			log(f"Migrating file '{filepath}' to '{newpath}'..", 'info')
			com = (f"cp \"{filepath}\" \"{newpath}\"")
			try:
				ret = subprocess.check_output(com, shell=True).decode().strip()
			except:
				ret = "pbdl.utils.migrate_movies:Unknown Error! ({filepath})!"
			if ret:
				log(f"Error migrating file: {filepath} to {newpath}. ({ret})", 'error')
				return False
			else:
				log(f"File moved!", 'info')
				if os.path.exists(newpath):
					com = (f"sqlite3 {db} \"update movies set filepath = \'{newpath}\' where id = {_id};\"")
					ret = subprocess.check_output(com, shell=True).decode().strip()
					if ret:
						log(f"Error renaming file in database: id={_id}", 'error')
						return False
				else:
					log(f"Error migrating file: {filepath} to {newpath}. (File not found!)", 'error')
					return False

def get_torrents_kerploosh():
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
					torrents[tid]['air_date'] = '11-11-1111'
			
	return torrents

def get_torrents_older():
	com = "transmission-remote -l | grep -v \"ID\" | grep -v \"Sum\""
	try:
		lines = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	except:
		return {}
	torrents = {}
	for line in lines:
		tid = int(line.strip().split(' ')[0])
		torrents[tid] = {}
		torrents[tid]['tid'] = tid
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
		try:
			torrents[tid]['name'] = line.split(status)[1].strip()
		except Exception as e:
			log(f"pbdl.utils.get_torrents():Unable to get torrent status ({e}, line={line}", 'error')
			torrents[tid]['name'] = line
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


def empty(tid):
	d = {}
	d['tid'] = tid
	d['percent'] = 'Unknown'
	d['have'] = 'Unknown'
	d['eta'] = 'Unknown'
	d['upload'] = 'Unknown'
	d['download'] = 'Unknown'
	d['ratio'] = 'Unknown'
	d['status'] = 'Unknown'
	d['name'] = 'Unknown'
	return d

def get_torrents_weirdness():
	com = f"transmission-remote -l | grep -v \"Ratio\" | grep -v \"Sum:\" | cut -d ' ' -f 4"
	tids = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	torrents = {}
	for tid in tids:
		torrents[int(tid)] = empty(tid)
	com = "transmission-remote -l | grep -v \"Ratio\" | grep -v \"Sum:\""
	lines = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	for line in lines:
		tid = int(line.strip().split(' ')[0].strip())
		torrents[tid] = {}
		percent = line.split(f"{tid} ")[1].strip().split(' ')[0]
		try:
			have = line.split(percent)[1].strip().split(' ')[0]
		except:
			have = percent.split(' ')[1]
			percent = percent.split(' ')[0]
		size_unit = line.strip().split(percent)[1].strip().split(' ')[1]
		if '100' in percent:
			eta = 'Done'
		else:
			eta = line.strip().split(size_unit)[1].strip().split(' ')[0]
		if have == '':
			have = 'Unknown'
		if eta == '':
			eta = 'Unknown'
			time_unit = 'Unknown'
		if eta != 'Unknown':
			time_unit = line.strip().split(eta)[1].strip().split(' ')[0]
			eta = f"{eta} {time_unit}"
		try:
			upload_speed = line.strip().split(eta)[1].strip().split(' ')[0]
		except Exception as e:
			upload_speed = eta.split(' ')[0]
			eta = eta.split(' ')[1]
			#upload_speed = line.strip().split(eta)[1]
			log(f"pbdl.utils.get_torrents():Cannot get upload speed ({e})!", 'error')
		if upload_speed == '':
			upload_speed = 'Unknown'
		download_speed = line.strip().split(upload_speed)[1].strip().split(' ')[0]
		if download_speed == '':
			download_speed = 'Unknown'
		ratio = line.strip().split(download_speed)[1].strip().split(' ')[0]
		if 'Downloading' in line:
			status = 'Downloading'
		elif 'Finished' in line:
			status = 'Done'
		elif 'Stopped' in line:
			status = 'Stopped'
		elif 'Up & Down' in line:
			status = 'Up & Down'
		else:
			status = 'Unknown'
		name = line.split(status)[1].strip()
		torrents[tid]['tid'] = tid
		torrents[tid]['percent'] = percent
		torrents[tid]['have'] = f"{have} {size_unit}"
		torrents[tid]['eta'] = eta
		torrents[tid]['upload_speed'] = upload_speed
		torrents[tid]['download_speed'] = download_speed
		torrents[tid]['ratio'] = ratio
		torrents[tid]['status'] = status
		torrents[tid]['name'] = name
		com = "transmission-remote -t1 -f | grep \"Yes\""
		files = subprocess.check_output(com, shell=True).decode().strip().split("\n")
		torrents[tid]['files'] = {}
		fid = -1
		for line in files:
			fid += 1
			torrents[tid]['files'][fid] = {}
			downloaded = line.strip().split('Yes')[1].strip().split(' ')[0]
			size_unit = line.split(downloaded)[1].strip().split(' ')[0]
			downloaded = f"{downloaded} {size_unit}"
			filepath = line.split(size_unit)[1].strip()
			torrents[tid]['files'][fid]['downloaded'] = downloaded
			torrents[tid]['files'][fid]['filepath'] = filepath
	return torrents

def get_files(tid):
	com = (f"transmission-remote {conf['pbdl']['remote_ip']} -t{tid} -f | grep -v \'Subs\' | grep -v \'Sample\' | grep -v '.png' | grep -v \'files):\' | grep -v \'#\' | grep -v \".jpg\" | grep -v \"sample\" | grep -v \".srt\" | grep -v \".nfo\" | grep -v \".txt\" | cut -d \"{os.path.sep}\" -f 2")
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

def sqlite3(query):
	#raise Exception('toaster', query)
	log(f"sqlite3 query running from utils.py, query={query}", 'info')
	try:
		if '%20' in query:
			query = urllib.parse.unquote(query)
		dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
		com = (f"sqlite3 '{dbfile}' \"{query}\"")
		out = subprocess.check_output(com, shell=True).decode().strip().split("\n")
		try:
			if MP.conf['debug'] == True:
				log(f"SQLITE3 Query: {query}", 'info')
				log(f"SQLITE3 Results: {out}", 'info')
		except:
			log(f"SQLITE3 Query: {query}", 'info')
			log(f"SQLITE3 Results: {out}", 'info')
		return out
	except:
		return []


def test_media_type(filepath):
	if '.mp3' in filepath:
		return 'music'
	if '/Series/' in filepath:
		return 'series'
	elif '/Music/' in filepath:
		return 'music'
	elif '/Movies/' in filepath:
		return 'movies'
	else:
		fname = os.path.basename(filepath)
		#if filepath looks like an actual filepath...
		#check to see if in database
		is_series = se_isin(fname)
		if is_series:
			return 'series'
		is_movie = ty_isin(fname)
		if is_movie:
			return 'movies'
		#print("is_series, is_movie:", is_series, is_movie)
		if conf['media_directories']['music'] in filepath:
			return 'music'
		try:
			is_music = sqlite3(f"select id from music where filepath like '%{filepath}%';")
			if is_music == ['']:
				is_music = False
			else:
				is_music = True
		except:
			is_music = False
		if not is_music and not is_movie and not is_series:
			#log(f"Error: Unknown type, couldn't parse keys from filepath! File: {filepath}", 'error')
			txt = f"Error: Unknown type, couldn't parse keys from filepath! File: {filepath}. Assuming video playlist..."
			return 'videos'
			#return False
	


def test_media(query, return_data=False):
	if type(query) == int:
		play_type, filepath = test_type_from_db(query)
	else:
		filepath = query
		play_type = test_media_type(filepath)
	if return_data == False:
		return play_type
	elif return_data == True:
		if play_type == 'series':
			return parse_series(filepath)
		elif play_type == 'movies':
			title, year = ty_isin(filepath, True)
			if 'ALTERNATE' in title:
				title = title.split('ALTERNATE')[0].strip()
			return [title, year]
		elif play_type == 'music':
			return parse_music(filepath)

def test_type_from_db(_id):
	#helper function to get media type from id when filepath not immediately available
	inseries = sqlite3(f"select filepath from series where id = '{_id}';")[0]
	inmovies = sqlite3(f"select filepath from movies where id = '{_id}';")[0]
	inmusic = sqlite3(f"select filepath from music where id = '{_id}';")[0]
	if inseries != '':
		return 'series', inseries
	elif inmovies != '':
		return 'movies', inmovies
	elif inmusic  != '':
		return 'music', inmusic

def parse_music(filepath):
	tag = id3.read(filepath)
	return tag.title, tag.artist, tag.album

def parse_series(filepath):
	conf = readConf()
	media_dir = conf['media_directories']['main']
	if media_dir in filepath:
		try:
			s, e, sinfo = se_isin(filepath, True)
			n = os.path.dirname(filepath).split(f"{media_dir}{os.path.sep}Series{os.path.sep}")[1].split(os.path.sep)[0]
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
			try:
				if data['results'] == True:
					log("Lookup successful!", 'info')
					return data
			except:
				print("data:", data)


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


def files_empty(filepath):
	play_type = test_media_type(filepath)
	d = {}
	d['play_type'] = play_type
	for key in list(get_columns(play_type).keys()):
		d[key] = None
	d['play_type'] = play_type
	d['lookup_type'] = '-TMDB-'
	return d


def get_torrents():
	com = "transmission-remote -l | grep -v \"Ratio\" | grep -v \"Sum:\""
	try:
		lines = subprocess.check_output(com, shell=True).decode().strip().split("\n")
	except:
		lines = []
		log(f"pbdl.get_torrents:List is probably empty!", 'warning')
		return {}
	#lines = ['25     2%   47.02 MB  5 hrs        0.0   240.0    0.0  Downloading  Captain America - The First Avenger (2011)', '  26     2%   60.29 MB  Unknown      0.0     0.0    0.0  Downloading  Captain.Marvel.2019.1080p.BRRip.x264-MkvCage.ws.mkv', '  27     0%    9.30 MB  2 hrs        0.0   119.0    0.0  Downloading  Iron Man [1080p]', '  28   100%    1.72 GB  Done         0.0     0.0    0.0  Stopped      Iron Man 2 (2010) [1080p]', '  29     6%   123.1 MB  17 hrs       0.0     0.0    0.0  Downloading  The Incredible Hulk (2008) [1080p]', '  30     1%   42.64 MB  2965 days     0.0     0.0    0.0  Downloading  Thor.2011.1080p.BluRay.H264.AAC-RARBG', "  31    n/a       None  Unknown      0.0     0.0   None  Idle         Marvel's+The+Avengers+(2012)(Bitloks)(1920).mkv", '  32     5%   99.85 MB  Unknown      0.0     0.0    0.0  Downloading  Thor The Dark World (2013) [1080p]', '  33    20%   419.7 MB  52 days      0.0     1.0    0.0  Downloading  Iron Man 3 (2013) [1080p]', '  34     6%   140.3 MB  47 min       0.0  1153.0    0.0  Up & Down    Captain America The Winter Soldier (2014) [1080p]', '  35     3%   68.42 MB  22 hrs       0.0     6.0    0.0  Downloading  Guardians of the Galaxy (2014) [1080p]', '  36     0%   49.15 kB  Unknown      0.0     0.0    0.0  Queued       Guardians of the Galaxy Vol. 2 (2017) 720p BrRip x264 - VPPV', '  37    n/a       None  Done         0.0     0.0   None  Queued       Avengers:+Age+of+Ultron+(2015)+1080p+BrRip+x264+-+YIFY', '  38     0%   524.3 kB  Unknown      0.0     0.0    0.0  Queued       Avengers Infinity War (2018) [BluRay] [1080p] [YTS.AM]', '  39    n/a       None  Done         0.0     0.0   None  Queued       Captain+America+Civil+War+2016+1080p+BluRay+x264+DTS-JYK', '  40    n/a       None  Done         0.0     0.0   None  Queued       Black.Panther.2018.1080p.BRRip.x264-BRRIP', '  41    n/a       None  Done         0.0     0.0   None  Queued       Spider-Man.Homecoming.2017.720p.BluRay.x264-NeZu', '  42    n/a       None  Done         0.0     0.0   None  Queued       Thor+Ragnarok+2017+1080p+HDRip+x264+AAC+5.1+ESub+-xRG', '  43     0%       None  Unknown      0.0     0.0   None  Queued       Avengers Endgame (2019) [BluRay] [1080p] [YTS.LT]', '  44     0%       None  Unknown      0.0     0.0   None  Queued       The Good The Bart And The Loki (2021) [1080p] [WEBRip] [5.1] [YTS.MX]', '  45    n/a       None  Done         0.0     0.0   None  Queued       What.If.2021.S01.COMPLETE.720p.DSNP.WEBRip.x264-GalaxyTV', '  46     0%   86.83 MB  Unknown      0.0     0.0    0.0  Idle         WandaVision (2021) Season 1 S01 (1080p DSNP WEB-DL x265 HEVC 10bit EAC3 5.1 Silence)', '  47    n/a       None  Done         0.0     0.0   None  Queued       The+Falcon+and+the+Winter+Soldier+(2021)+Season+1+S01+(1080p+WEB', '  48    n/a       None  Done         0.0     0.0   None  Queued       Shang-Chi+and+the+Legend+of+the+Ten+Rings+(2021)+[1080p]+[BluRay', '  49    n/a       None  Done         0.0     0.0   None  Queued       Eternals+(2021)+[1080p]+[WEBRip]+[5.1]', '  50    n/a       None  Done         0.0     0.0   None  Queued       Hawkeye+2021+S01E01+Never+Meet+Your+Heroes+1080p+DSNP+WEB-DL+DDP', '  51    n/a       None  Done         0.0     0.0   None  Queued       Moon.Knight.2022.S01.2160p.10bit.DSNP.DDP5.1.HEVC.x265-Vyndros', '  52    n/a       None  Done         0.0     0.0   None  Queued       She-Hulk+Attorney+at+Law+(2022)+Season+1+S01+(1080p+DSNP+WEB-DL+x265+HEVC+10bit', '  53    n/a       None  Done         0.0     0.0   None  Queued       Ms.Marvel.2022.S01.2160p.10bit.DSNP.DDP5.1.HEVC.x265-Vyndros', '  54    n/a       None  Done         0.0     0.0   None  Queued       Thor+Love+and+Thunder+(2022)+[1080p]+[WEBRip]+[5.1]']
	statuses = ['Queued', 'Downloading', 'Idle', 'Stopped', 'Finished', 'Up & Down']
	torrents = {}
	for line in lines:
		tid = int(line.strip().split(' ')[0].strip())
		percent = line.split(f"{tid} ")[1].strip().split(' ')[0]
		have = line.split(percent)[1].strip().split(' ')[0]
		if have != 'None':
			size_unit = line.split(have)[1].strip().split(' ')[0]
			have = f"{have} {size_unit}"
		eta = line.split(have)[1].strip().split(' ')[0]
		if eta != 'Unknown' and eta!= 'Done':
			time_unit = line.split(f"{eta} ")[1].strip().split(' ')[0]
			if '%' in time_unit:
				time_unit = line.split(f"{eta} ")[2].strip().split(' ')[0]
			eta = f"{eta} {time_unit}"
		if have != 'None':
			uploaded = line.split(eta)[1].strip().split(' ')[0]
			downloaded = line.split(f"{uploaded} ")[1].strip().split(' ')[0]
			try:
				ratio = line.split(f"{downloaded} ")[1].strip().split(' ')[0]
			except:
				ratio = 0.0
		else:
			uploaded = '0.0'
			downloaded = '0.0'
			ratio = 'None'
		status = None
		for s in statuses:
			if s in line:
				status = s
		name = line.split(status)[1].strip()
		if tid is not None and percent is not None and have is not None and eta is not None and uploaded is not None and downloaded is not None and ratio is not None and status is not None and name is not None:
			torrents[tid] = {}
			torrents[tid]['tid'] = tid
			torrents[tid]['percent'] = percent
			torrents[tid]['have'] = have
			torrents[tid]['eta'] = eta
			torrents[tid]['uploaded'] = uploaded
			torrents[tid]['downloaded'] = downloaded
			torrents[tid]['ratio'] = ratio
			torrents[tid]['status'] = status
			torrents[tid]['name'] = name
			files = get_files(tid)
			torrents[tid]['files'] = {}
			if files != []:
				for filepath in files:
					torrents[tid]['files'][filepath] = {}
					torrents[tid]['files'][filepath]['filepath'] = filepath
	return torrents



def build_data(rebuild=False, lookup_type=None):
	
	if lookup_type == None:
		lookup_type = '-TMDB-'
	if rebuild is False:
		log(f"Loading saved data...", 'info')
		try:
			torrents = load_saved_data()
		except Exception as e:
			log(f"pbdl.utils.build_data:Unable to load data! {e}", 'error')
			torrents = get_torrents()
		if torrents is not None:
			return torrents
		else:
			torrents = get_torrents()
	elif rebuild is True:
		torrents = get_torrents()
	for tid in torrents.keys():
		files = get_files(tid)
		torrents[tid]['files']  = {}
		for filepath in files:
			play_type = test_media(filepath)
			query_info = test_media(filepath, True)
			log(f"filepath:{filepath}, play_type:{play_type}, query_info:{query_info}", 'info')
			try:
				results = torrents[tid]['files'][filepath]['info']['results']
			except Exception as e:
				log(f"Results tag not found: {e}", 'warning')
				results = None
			if results is None:
				torrents[tid]['files'][filepath] = {}
				torrents[tid]['files'][filepath]['info'] = set_empty(play_type)
				torrents[tid]['files'][filepath]['info']['filepath'] = filepath
				torrents[tid]['files'][filepath]['info']['play_type'] = play_type
				if torrents[tid]['files'][filepath]['info']['play_type'] == 'series':
					torrents[tid]['files'][filepath]['info']['series_name'], torrents[tid]['files'][filepath]['info']['season'], torrents[tid]['files'][filepath]['info']['episode_number'] = query_info
					series_name, season, episode_number = test_media(filepath, True)
					tname = verify_series_name(series_name)
					if tname is not None:
						series_name = tname
					torrents[tid]['air_date'] = '11-11-1111'
					torrents[tid]['files'][filepath]['info']['series_name'] = series_name
					torrents[tid]['files'][filepath]['info']['season'] = season
					torrents[tid]['files'][filepath]['info']['episode_number'] = episode_number
					torrents[tid]['files'][filepath]['info']['lookup_type'] = lookup_type
				elif torrents[tid]['files'][filepath]['info']['play_type'] == 'movies':
					torrents[tid]['files'][filepath]['info']['title'] = query_info[0]
					title, year = test_media(filepath, True)
					log(f"filepath:{filepath}, data:{test_media(filepath, True)}", 'info')
					torrents[tid]['files'][filepath]['info']['title'] = title
					torrents[tid]['files'][filepath]['info']['year'] = year
					torrents[tid]['files'][filepath]['info']['lookup_type'] = lookup_type
				try:
					ret = lookup(torrents[tid]['files'][filepath]['info'])
				except Exception as e:
					log(f"pbdl.utils.build_data():Can't get info... {e}", 'info')
				try:
					if ret['results'] == True:
						torrents[tid]['files'][filepath]['info'] = ret
						torrents[tid]['files'][filepath]['info']['filepath'] = filepath
				except Exception as e:
					log(f"Unable to get info for filepath {filepath}: {e}", 'warning')
	save_data(torrents)
	return torrents


def get_id(filepath, play_type=None):
	fname = os.path.basename(filepath)
	if play_type is None:
		play_type = test_media(filepath)
	return sqlite3(f"select id from {play_type} where filepath like '%{fname}%';")[0]

def get_filepath(_id, play_type):
	return sqlite3(f"select filepath from {play_type} where id = {_id};")[0]


def get_play_type(filepath):
	log(f"self.get_play_type running...", 'info')
	layout = []
	window_title = 'Select play type:'
	fname_line = [sg.Text(f"Setting info for:{filepath}...")]
	play_type_combo = [sg.Combo(['series', 'movies', 'music'], 'series', enable_events=True,key='-PLAY_TYPE-')]
	submit = [sg.Button('Submit')]
	layout.append(play_type_combo)
	layout.append(fname_line)
	layout.append(submit)
	win_key = window_title.lower().replace(' ', '_')
	win = sg.Window(window_title, layout, size=(300, 100), keep_on_top=False, element_justification='center', finalize=True)
	data = None
	while True:
		event, values = win.read()
		if event == sg.WIN_CLOSED:
			break
		else:
			play_type = values[event]
			win.close()
	log(f"play_type:{play_type}", 'info')
	return play_type


#use series poster as failover, choose still_path if available
def get_poster(query):
	if type(query) == int:
		play_type = test_media(query)
		filepath = get_filepath(query, play_type)
	elif type(query) == str:
		filepath = query
	play_type = test_media(filepath)
	if play_type == 'series':
		column = 'still_path'
	elif play_type == 'movies' or play_type == 'music':
		column = 'poster'
	fname = os.path.basename(filepath)
	indb = sqlite3(f"select {column} from {play_type} where filepath like '%{fname}%';")[0]
	print(f"sqlite3 query poster results(query={query}): {indb}", 'info')
	baseurl = None
	if indb == 'No image data available.' or indb == 'null' or indb == '' or indb == 'Unknown' or 'Unknown' in indb:
		url = None
	else:
		url = indb
	if url is not None:
		#return early if database has path.
		return f"https://image.tmdb.org/t/p/original{url}"
	#grab url from tmdb if not in database.
	data = test_media(filepath, True)
	if play_type == 'series':
		series_name, season, episode_number = data
		info = query_series(series_name, season, episode_number)
		url = info['still_path']
		print(f"(tmdb_query_series) url:{url}")
	elif play_type == 'movies':
		title, year = data
		info = query_movies(title)
		print("info:", info)
		url = info['poster']
		print(f"(tmdb_query_movies) url:{url}")
	poster = f"https://image.tmdb.org/t/p/original{url}"
	#update database
	ret = sqlite3(f"update {play_type} set {column} = \'{poster}\' where filepath like '%{fname}%';")
	if ret != ['']:
		log(f"pbdl.utils.get_poster:Encountered an error updating poster in database: {ret}", 'error')
	else:
		log(f"pbdl.utils.get_poster:Updated database: (poster={poster})", 'info')
	return poster

def dl_poster(poster_url):
	poster_path = os.path.join(os.path.expanduser("~"), '.np', 'poster.jpg')
	com = f"curl -o \"{poster_path}\" {poster_url}"
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret != '':
		print(f"Error downloading poster ({poster_url}): {ret}", 'error')
		return poster_path
	else:
		print("Ok!")
		return poster_path

def convert_png(filepath, w=None, h=None):
	if w is None:
		w = 320
	if h is None:
		h = 240
	size = f"{w}x{h}"
	ext = os.path.splitext(filepath)[1]
	dname = os.path.dirname(filepath)
	fname = os.path.basename(os.path.splitext(filepath)[0])
	newpath = os.path.join(dname, f"{fname}.png")
	#com = (f"convert --resize \"{filepath}\" \"{newpath}\"")
	com = f"convert \"{filepath}\" -resize {size} \"{newpath}\""
	#com = ("convert 'poster.jpg' -resize " + str(self.art_w) + "x" + str(self.art_h) + " 'poster.png'")
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret != '':
		print(f"Error converting jpg to png: {ret}", 'error')
		return False
	else:
		print("Ok!")
		return newpath


def test_series_name(series_name):
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	com = f"sqlite3 \"{dbfile}\" \"select distinct series_name from series where series_name like '%{series_name}%' COLLATE NOCASE;\""
	ret = subprocess.check_output(com, shell=True).decode().strip()
	if ret != '':
		return ret
	else:
		log(f"pbdl.utils.test_series_name: Failed to find name: {series_name}!", 'error')
		return None
		

if __name__ == "__main__":
	data = build_torrents()
	log(data, 'info')
