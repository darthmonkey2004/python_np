import subprocess
import json
import requests
from np import log, DATA_DIR, readConf

def rt_series(series_name=None, season=None, episode_number=None):
	if series_name is None:
		log(f"Error: No series name provided!", 'error')
		return None
	else:
		if ' ' in series_name:
			s = ' '
			chunks = series_name.split(s)
			j = '_'
			query = j.join(chunks).lower()
		else:
			query = series_name.lower()
		url = f"https://rtv2-production-2-6.rottentomatoes.com/tv/{query}"
	if season is not None:
		l = len(str(season))
		if len == 1:
			s_query = f"s0{season}"
		else:
			s_query = f"s{season}"
		url = f"https://rtv2-production-2-6.rottentomatoes.com/tv/{query}/{s_query}"
	if episode_number is not None:
		l = len(str(episode_number))
		if len == 1:
			e_query = f"e0{episode_number}"
		else:
			e_query = f"e{episode_number}"
		url = f"https://rtv2-production-2-6.rottentomatoes.com/tv/{query}/{s_query}/{e_query}"
	r = requests.get(url)
	if r.status_code == 200:
		data = r.text
	else:
		log(f"Bad response code:{r.status_code}", 'error')
		return None
	s = '<script type="application/ld+json" id="jsonLdSchema">'
	try:
		json_string = data.split(s)[1].split('</script>')[0]
		json_data = json.loads(json_string)
		info['poster'] = json_data['image']
		print (info['poster'])
	except:
		pass
	return data


#def get_episode_data(series_name, season, episode_number):
#	title_tag = 'class="noSpacing movie_title">'
#	description_tag = 'id="movieSynopsis"'
#	poster_tag = 'class="posterImage"'
#	# air date is one line down from tag
#	air_date_tag = 'Air Date: '
#	data = rt_series(series_name, season, episode_number).split("\n")
#	lines=len(data)
#	pos = -1
#	info = {}
#	info['title'] = 'Unknown'
#	info['description'] = 'Unknown'
#	info['poster'] = 'Unknown'
#	info['air_date'] = 'Unknown'
#	for line in data:
#		pos += 1
#		if title_tag in line:
#			info['title'] = line.split(title_tag)[1].split('<')[0]
#		if description_tag in line:
#			newpos = pos + 1
#			info['description'] = data[newpos].strip().split("<")[0]
#		if poster_tag in line:
#			info['poster'] = line.split('<img src="')[1].split('"')[0]
#		if air_date_tag in line:
#			new_pos = pos + 1
#			info['air_date'] = data[new_pos].split('"meta-value">')[1].split('<')[0]
#	return info

def get_episode_data(series_name, season, episode_number, filepath=None):
	if filepath is None:
		com = (f"sqlite3 \"{DATA_DIR}/nplayer.db\" \"select filepath from series where series_name like \'%{series_name}%\' and season = {season} and episode_number = {episode_number};\"")
		filepath = subprocess.check_output(com, shell=True).decode().strip()
		if filepath == '':
			conf = readConf()
			_dir = conf['media_directories']['main']
			listfile = (f"{_dir}/medialist.txt")
			string = (f"Series/{series_name}/S{season}")
			com = (f"cat \"{listfile}\" | grep \"{string}\" | grep \"S{season}E{episode_number}\"")
			filepath = subprocess.check_output(com, shell=True).decode().strip()
			if filepath == '':
				log(f"Unable to get filepath with given details.")
				filepath = 'Unknown'
	episodes_split = '<script type="application/ld+json" id="jsonLdSchema">'
	data = rt_series(series_name, season, episode_number).split(episodes_split)[1].split('</script>')[0]
	json_data = json.loads(data)
	info = {}
	info['series_name'] = series_name
	info['season'] = season
	info['episode_number'] = episode_number
	info['episode_name'] = json_data['name']
	info['description'] = json_data['description']
	info['air_date'] = json_data['partOfSeries']['startDate']
	info['isactive'] = 1
	info['filepath'] = filepath
	info['still_path'] = json_data['image'][0]['url']
	info['url'] = json_data['url']
	return info
	
	
def get_season_data(series_name, season):
	episodes_split = '<script type="application/ld+json" id="jsonLdSchema">'
	data = rt_series(series_name, season).split(episodes_split)[1].split('</script>')[0]
	data = json.loads(data)
	json_data = data['episode']
	info = {}
	
	for e in json_data:
		fpath = (f"")
		episode_data = {}
		episode_number = e['episodeNumber']
		episode_data['episode_number'] = episode_number
		episode_data['series_name'] = series_name
		episode_data['season'] = season
		episode_data['episode_name'] = e['name']
		episode_data['description'] = e['description']
		episode_data['air_date'] = data['partOfSeries']['startDate']
		episode_data['isactive'] = 1
		episode_data['filepath'] = None
		episode_data['url'] = e['url']
		episode_data['still_path'] = 'Unknown'
		info[episode_number] = episode_data
	return info


def get_all_series_data(series_name):
	all_data = {}
	seasons = get_seasons(series_name)
	for season in seasons:
		season_data = get_season_data(series_name, season)
		all_data[season] = season_data
	return all_data

def get_seasons(series_name):
	episodes_split = '<script type="application/ld+json" id="jsonLdSchema">'
	data = rt_series(series_name).split(episodes_split)[1].split('</script>')[0]
	json_data = json.loads(data)
	seasons_data = json_data['containsSeason']
	seasons = []
	for season in seasons_data:
		season = season['url'].split('/')[3].split('s')[1]
		if '0' in season:
			try:
				first = season[0]
				second = season[1]
				if first == '0':
					season = int(second)
				else:
					season = int(f("{first}{second}"))
			except:
				season = int(season)
		else:
			season = int(season)
		seasons.append(season)
	seasons = sorted(seasons)
	return seasons
	
		

def rt_movies(title):
	if title is None:
		log(f"Error: No title provided!", 'error')
		return None
	else:
		if ' ' in title:
			s = ' '
			chunks = title.split(s)
			j = '_'
			query = j.join(chunks).lower()
		else:
			query = title.lower()
		url = f"https://rtv2-production-2-6.rottentomatoes.com/m/{query}"
	r = requests.get(url)
	if r.status_code == 200:
		data = r.text
	else:
		log(f"Bad response code:{r.status_code}", 'error')
		return None
	s = '<script type="application/ld+json" id="jsonLdSchema">'
	try:
		json_string = data.split(s)[1].split('</script>')[0]
		json_data = json.loads(json_string)
		info['poster'] = json_data['image']
	except:
		pass
	return data

def get_movie_data(title):
	info = {}
	data = rt_movies(title).split("\n")
	description_tag = 'id="movieSynopsis"'
	poster_tag = 'class="posterImage"'
	year_tag = '<time datetime="'
	pos = -1
	info['description'] = 'Unknonw'
	info['year'] = 'Unknown'
	info['poster'] = 'Unknown'
	for line in data:	
		pos += 1
		if description_tag in line:
			newpos = pos + 1
			info['description'] = data[newpos].strip().split("<")[0]
		if poster_tag in line:
			info['poster'] = line.split('<img src="')[1].split('"')[0]
		if year_tag in line and info['year'] == 'Unknown':
			string = line.split('>')[1].split('<')[0].split(' ')[2]
			info['year'] = string
	return info
