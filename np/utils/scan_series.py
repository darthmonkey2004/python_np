from os.path import basename
from np import test_db, readConf, log, addtodb
import subprocess
import urllib
import requests
import json

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
		print ("Error getting tmdbid:", e)
	try:
		still_path = json_data['results'][0]['backdrop_path']
	except Exception as e:
		print ("Still path was error:", e)
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
	if "'" in info['description']:
		chunks = info['description'].split("'")
		d=''
		info['description'] = d.join(chunks)
	if "'" in info['series_name']:
		chunks = info['series_name'].split("'")
		d=''
		info['series_name'] = d.join(chunks)
	if "'" in info['episode_name']:
		chunks = info['episode_name'].split("'")
		d=''
		info['episode_name'] = d.join(chunks)

	return info

def scan_series(target_dir=None):
	type = 'series'
	exts = ['mp4', 'mov', 'avi', 'flv']
	test_db()
	conf = readConf()
	if target_dir == None:
		target_dir = conf['media_directories']['series']
	for ext in exts:
		com = (f"find '{target_dir}' -name '*.{ext}'")
		files = subprocess.check_output(com, shell=True).decode().strip()
		files = files.split("\n")
		for filepath in files:

			try:
				fname = basename(filepath)
				l = len(fname) - 4
				fname = fname[:l]
				if '.' in fname:
					fname = fname.split('.')
					d=' '
					fname = d.join(fname)
				parsed_series_name = fname.split(' ')[0]
				sinfo = fname.split(' ')[1]
				parsed_season = sinfo.split('E')[0].split('S')[1]
				parsed_episode_number = sinfo.split('E')[1]
				sp = (f"{series_name} S{season}E{episode_number} ")
				parsed_episode_name = fname.split(sp)[1]

			except Exception as e:
				print (f"Exception: {e}")
				print (f"Filepath: {filepath}")
				s = (f"{target_dir}/series")
				series_name = filepath.split(target_dir)[1].split('/')[1]
				season = filepath.split(target_dir)[1].split('/')[2].split('S')[1]
				episode_number = input ("Enter episode number: ")
			
			info = query_series(filepath, series_name, season, episode_number)
			sql_string = (f"INSERT INTO series (isactive, series_name, tmdbid, season, episode_number, episode_name, description, air_date, still_path, filepath) VALUES('{info['isactive']}', '{info['series_name']}', '{info['tmdbid']}', '{info['season']}', '{info['episode_number']}', '{info['episode_name']}', '{info['description']}', '{info['air_date']}', '{info['still_path']}', '{info['filepath']}');")
			if info['error'] == False:
				out = (f"Added to series: Name - {info['series_name']}, S{info['season']}E{info['episode_number']}")
				log(out, 'info')
			else:
				out = (f"Lookup failed for file '{info['filepath']}': Response='{info['response']}'. Adding generic values insteal...")
				log(out, 'warning')
				if parsed_series_name is not None:
					info['series_name'] = parsed_series_name
				if parsed_season is not None:
					info['season'] = parsed_season
				if parsed_episode_number is not None:
					info['episode_number'] = parsed_episode_number
				if parsed_episode_name is not None:
					info['episode_name'] = parsed_episode_name
			ret = addtodb('series', sql_string)
			if ret is not True:
				print (f"Error:{ret}, Data:{info}")
				input("Press a key...")
			

if __name__ == "__main__":
	import sys
	target_dir = sys.argv[1]
	scan_music(target_dir)
