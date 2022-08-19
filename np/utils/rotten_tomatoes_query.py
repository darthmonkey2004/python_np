import json
import requests

def rt_series(series_name=None, season=None, episode_number=None):
	if series_name is None:
		np.log(f"Error: No series name provided!", 'error')
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
		np.log(f"Bad response code:{r.status_code}", 'error')
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


def get_episode_data(series_name, season, episode_number):
	title_tag = 'class="noSpacing movie_title">'
	description_tag = 'id="movieSynopsis"'
	poster_tag = 'class="posterImage"'
	# air date is one line down from tag
	air_date_tag = 'Air Date: '
	data = rt_series(series_name, season, episode_number).split("\n")
	lines=len(data)
	pos = -1
	info = {}
	info['title'] = 'Unknown'
	info['description'] = 'Unknown'
	info['poster'] = 'Unknown'
	info['air_date'] = 'Unknown'
	for line in data:
		pos += 1
		if title_tag in line:
			info['title'] = line.split(title_tag)[1].split('<')[0]
		if description_tag in line:
			newpos = pos + 1
			info['description'] = data[newpos].strip().split("<")[0]
		if poster_tag in line:
			info['poster'] = line.split('<img src="')[1].split('"')[0]
		if air_date_tag in line:
			new_pos = pos + 1
			info['air_date'] = data[new_pos].split('"meta-value">')[1].split('<')[0]
	return info
		
def get_season_data(series_name, season):
	episodes_split = 'class="episodes"'
	data = rotten_tomatoes_lookup(series_name, season, episode_number).split(episode_split)[1].split("\n")
	print (data)
	input()
	
def rt_movies(title):
	if title is None:
		np.log(f"Error: No title provided!", 'error')
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
		np.log(f"Bad response code:{r.status_code}", 'error')
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
