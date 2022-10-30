import os
from os.path import basename
from np.core.conf import readConf
from np.core.log import np_logger
from np import get_columns
from np import cleandb
import subprocess
import urllib
import requests
import json
log = np_logger().log_msg
conf = readConf()
data_dir = os.path.join(os.path.expanduser("~"), '.np')
def sqlite3(query):
	query = (query.replace("'", "\'").replace('"', '\"'))
	dbfile = os.path.join(data_dir, "nplayer.db")
	com = (f"sqlite3 '{dbfile}' \"{query}\"")
	out = subprocess.check_output(com, shell=True).decode().strip().split("\n")[0]
	if conf['debug'] == True:
		log(f"SQLITE3 Query: {query}", 'info')
		log(f"SQLITE3 Results: {out}", 'info')
	return out


def add_to_db(info):
	varslist = []
	outlist = []
	schema = get_columns('series')
	keys = list(schema.keys())
	for column in info.keys():
		if column in keys and column != 'id':
			varslist.append(column)
			val = info[column]
			dtype = schema[column]['data_type']
			if dtype == 'INTEGER' or dtype == 'BOOL':
				outlist.append(str(val))
			else:
				outlist.append(f"\'{val}\'")
	j = ", "
	keys = j.join(varslist)
	vals = j.join(outlist)
	query = f"INSERT INTO series ({keys}) VALUES ({vals});"
	ret = sqlite3(query)
	if ret:
		print("Query returned data (error???): {ret}")
		input()
		return False
	return True


def set_empty(filepath):
	info = {}
	schema = get_columns('series')
	columns = list(schema.keys())
	for column in columns:
		dtype = schema[column]['data_type']
		if dtype == 'INTEGER' or dtype == 'BOOL':
			if column != '_id':
				info[column] = 0
		else:
			info[column] = 'Unknown'
	return info

def query_series(filepath, series_name, season, episode_number):
	info = {}
	series_name_nw = urllib.parse.quote(series_name)
	API_KEY="ac1bdc4046a5e71ef8aa0d0bd93f8e9b"
	url = ("https://api.themoviedb.org/3/search/tv?api_key=" + str(API_KEY) + "&language=en-US&query=" + series_name_nw)
	r = requests.get(url)
	if r.status_code != 200:
		out = ("Error:", r.status_code)
		return out
	data = r.text
	json_data = json.loads(data)
	try:
		tmdbid = json_data['results'][0]['id']
	except Exception as e:
		log(f"Error getting tmdbid:{e}", 'error')
	try:
		still_path = json_data['results'][0]['backdrop_path']
	except Exception as e:
		log(f"Still path was error:{e}", 'error')
		still_path = json_data['results'][0]['poster_path']
	if "'" in json_data['results'][0]['name']:
		temp = json_data['results'][0]['name']
		temp = temp.split("'")
		j = "_"
		json_data['results'][0]['name'] = j.join(temp)
	url = "https://api.themoviedb.org/3/tv/" + str(tmdbid) + "/season/" + str(season) + "/episode/" + str(episode_number) + "?api_key=" + str(API_KEY) + "&language=en-US"
	r = requests.get(url)
	if r.status_code != 200:
		out = ("Error:", r.status_code, "URL:", url)
		info['error'] = True
		info['response'] = out
		info['filepath'] = filepath
		info['tmdbid'] = tmdbid
		info['series_name'] = series_name
		info['season'] = season
		info['episode_number'] = episode_number
		info['episode_name'] = 'null'
		info['description'] = 'null'
		info['air_date'] = 'null'
		info['still_path'] = 'null'
		info['duration'] = 'null'
		info['md5'] = 'null'
		info['isactive'] = 1
		info['url'] = url
	else:
		data = r.text
		json_data = json.loads(data)
		out = ("OK:", r.status_code, "URL:", url)
		info['error'] = False
		info['response'] = out
		info['filepath'] = filepath
		info['tmdbid'] = tmdbid
		info['series_name'] = series_name
		info['season'] = season
		info['episode_number'] = episode_number
		info['episode_name'] = json_data['name']
		info['description'] = json_data['overview']
		info['air_date'] = json_data['air_date']
		info['still_path'] = json_data['still_path']
		info['duration'] = 'null'
		info['md5'] = 'null'
		info['isactive'] = 1
		info['url'] = url
	info['description'] = info['description'].replace("'", "").replace('"', "")
	info['series_name'] = info['series_name'].replace("'", "").replace('"', "")
	info['episode_name'] = info['episode_name'].replace("'", "").replace('"', "")
	return info

def scan_series(target_dir=None):
	type = 'series'
	exts = ['mp4', 'mov', 'avi', 'flv', 'mkv', 'm4v']
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	if not os.path.exists(dbfile):
		print("Friggin' database doesn't exist? Fix it, Matt...")
	if target_dir == None:
		target_dir = conf['media_directories']['series']
	for ext in exts:
		com = (f"find '{target_dir}' -name '*.{ext}'")
		files = subprocess.check_output(com, shell=True).decode().strip()
		files = files.split("\n")
		for filepath in files:
			go = False
			series_name = None
			season = None
			episode_number = None
			fname = os.path.basename(filepath)
			com = (f"select filepath from series where filepath like '%{fname}%';")
			exists = sqlite3(com)
			if conf['debug'] == True:
				log(f"Exists: {exists}", 'info')
			if exists == '' or exists is None:
				if filepath != '' and filepath is not None:
					go = True
				else:
					go = False
					log(f"filepath not set!", 'warning')
			else:
				log(f"File already in database: '{filepath}'", 'info')
				go = False
			if go == True:
				try:
					fname = basename(filepath)
					l = len(fname) - 4
					fname = fname[:l]
					series_name = fname.split('.')[0]
					sinfo = fname.split('.')[1]
					season = sinfo.split('E')[0].split('S')[1]
					episode_number = sinfo.split('E')[1]
					episode_name = fname.split('.')[2]
					if conf['debug'] == True:
						log(f"series_name='{series_name}', season={season}, episode_number={episode_number}", 'info')

				except Exception as e:
					log(f"Exception:{e}, Filepath: {filepath}", 'error')
					s = (f"{target_dir}/series")
					series_name = input("Enter series name:")
					season = input("Enter season:")
					episode_number = input ("Enter episode number: ")
					episode_name = input ("Enter episode name: (blank for none)")
					if episode_name is None or episode_name == '':
						episode_name = 'Unknown'
			
				info = set_empty(filepath)
				if series_name is not None:
					info['series_name'] = series_name
				if season is not None:
					info['season'] = season
				if episode_number is not None:
					info['episode_number'] = episode_number
				if episode_name is not None:
					info['episode_name'] = episode_name
				info = query_series(filepath, series_name, season, episode_number)
				ret = add_to_db(info)
				if ret is not True:
					log(f"Error:{ret}, Data:{info}", 'error')
					input("Press a key...")



	log(f"Running cleandb: 'series'...", 'info')
	cleandb('series')
if __name__ == "__main__":
	import sys
	target_dir = sys.argv[1]
	scan_music(target_dir)
