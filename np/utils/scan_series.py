from np.utils.pbdl.utils import test_media
import os
from os.path import basename
from np.core.conf import readConf
from np.core.log import np_logger
from np import get_columns
from np import cleandb
from np.utils.pbdl.query_series import query_series
import subprocess
import urllib
import requests
import json
log = np_logger().log_msg
conf = readConf()
data_dir = os.path.join(os.path.expanduser("~"), '.np')
def sqlite3(query):
	log(f"sqlite3 query running from scan_series, query={query}", 'info')
	query = (query.replace("'", "\'").replace('"', '\"'))
	dbfile = os.path.join(data_dir, "nplayer.db")
	com = (f"sqlite3 '{dbfile}' \"{query}\"")
	out = subprocess.check_output(com, shell=True).decode().strip().split("\n")[0]
	if conf['debug'] == True:
		log(f"SQLITE3 Query: {query}, Results: {out}", 'info')
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



def scan_series(target_dir=None):
	type = 'series'
	exts = ['mp4', 'mov', 'avi', 'flv', 'mkv', 'm4v']
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	if not os.path.exists(dbfile):
		print("Friggin' database doesn't exist? Fix it, Matt...")
	if target_dir == None:
		target_dir = conf['media_directories']['series']
	for ext in exts:
		com = (f"find '{target_dir}' -name '*.{ext}' | grep -v \"Movies\"")
		try:
			files = subprocess.check_output(com, shell=True).decode().strip()
			files = files.split("\n")
		except Exception as e:
			log(f"scan_series.scan_series():No files found for ext:{ext}!", 'info')
			files = []
		ct = len(files)
		pos = 0
		for filepath in files:
			pos += 1
			try:
				print(f"progress: {pos}/{ct}...")
			except:
				pass
			log(f"progress: {pos}/{ct}", 'info')
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
				episode_name = None
				add = False
				try:
					series_name, season, episode_number = test_media(filepath, True)
					if conf['debug'] == True:
						log(f"series_name='{series_name}', season={season}, episode_number={episode_number}", 'info')
				except Exception as e:
					log(f"scan_series.scan_series():Error getting info:{e}", 'error')
			
				info = set_empty(filepath)
				if series_name is not None:
					info['series_name'] = series_name
				if season is not None:
					info['season'] = season
				if episode_number is not None:
					info['episode_number'] = episode_number
				if episode_name is not None:
					info['episode_name'] = episode_name
				try:
					info = query_series(series_name, season, episode_number)
					add = True
				except Exception as e:
					log(f"Error getting info! msg:{e}, filepath:{filepath}, series_name:{series_name}, season:{season}, episode_number:{episode_number}", 'error')
					add = False
				info['description'] = info['description'].replace("'", '').replace('"', '')
				info['episode_name'] = info['episode_name'].replace("'", '').replace('"', '')
				if add:
					info['filepath'] = filepath
					try:
						ret = add_to_db(info)
						if ret is not True:
							log(f"Error:{ret}, Data:{info}", 'error')
					except Exception as e:
						log(f"Error:{e}, info:{info}", 'error')



	log(f"Running cleandb: 'series'...", 'info')
	cleandb('series')
if __name__ == "__main__":
	import sys
	target_dir = sys.argv[1]
	scan_music(target_dir)
