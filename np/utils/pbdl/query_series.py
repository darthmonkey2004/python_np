import tmdbsimple as tmdb
tmdb.API_KEY = 'ac1bdc4046a5e71ef8aa0d0bd93f8e9b'

def get_series_id(series_name):
	search = tmdb.Search()
	r = search.tv(query=series_name)
	return r['results'][0]['id']

def get_seasons(_id):
	if type(_id) == str:
		_id = int(get_series_id(_id))
	data = tmdb.TV(_id).info()['seasons']
	info = {}
	for item in data:
		season = int(item['season_number'])
		info[season] = {}
		info[season]['tmdbid'] = item['id']
		info[season]['air_date'] = item['air_date']
		info[season]['episodes_ct'] = item['episode_count']
		info[season]['series_name'] = item['name']
		info[season]['description'] = item['overview']
		info[season]['poster'] = f"https://image.tmdb.org/t/p/original{item['poster_path']}"
	return info

def get_season_data(_id, season):
	season = int(season)
	if type(_id) == str:
		series_name = str(_id)
		_id = int(get_series_id(series_name))
	else:
		series_name = 'Unknown'
	try:
		s = tmdb.TV_Seasons(_id, season).info()
	except Exception as e:
		print(f"Error looking up season:{season} ({e})", 'error')
		return {}
	info = {}
	info[season] = {}
	for k in s.keys():
		if k == 'episodes':
			info[season]['episodes'] = {}
			for item in s[k]:
				episode_number = int(item['episode_number'])
				info[season]['episodes'][episode_number] = {}
				info[season]['episodes'][episode_number]['air_date'] = item['air_date']
				info[season]['episodes'][episode_number]['unique_id'] = item['id']
				info[season]['episodes'][episode_number]['episode_name'] = item['name']
				info[season]['episodes'][episode_number]['description'] = item['overview']
				info[season]['episodes'][episode_number]['season'] = item['season_number']
				info[season]['episodes'][episode_number]['still_path'] = f"https://image.tmdb.org/t/p/original{item['still_path']}"
				info[season]['episodes'][episode_number]['guest_stars'] = item['guest_stars']
				info[season]['episodes'][episode_number]['tmdbid'] = _id
				info[season]['episodes'][episode_number]['isactive'] = 1
				info[season]['episodes'][episode_number]['season'] = season
				info[season]['episodes'][episode_number]['episode_number'] = episode_number
		elif 'path' in k:
			info[season][k] = f"https://image.tmdb.org/t/p/original{s[k]}"
		else:
			info[season][k] = s[k]
	if series_name is not None:
		info['series_name'] = series_name
	return info

def get_episode_data(_id, season, episode_number):
	season = int(season)
	episode_number = int(episode_number)
	if type(_id) == str:
		series_name = str(_id)
		_id = int(get_series_id(series_name))
	info = get_season_data(_id, season)
	out = info[season]['episodes'][episode_number]
	out['results'] = True
	return out

def get_all_series_data(query='Disenchantment'):
	_id = get_series_id(query)
	seasons = get_seasons(_id)
	info = {}
	info[_id] = {}
	info[_id]['series_name'] = series_name
	info[_id]['seasons'] = get_seasons(_id)
	for season in info[_id]['seasons'].keys():
		info[_id]['seasons'] = get_season_data(_id, season)
	return info


def query_series(series_name, season=None, episode_number=None):
	if season is not None and episode_number is not None:
		return get_episode_data(series_name, season, episode_number)
	elif season is not None and episode_number is None:
		return get_season_data(series_name, season)
	elif season is None and episode_number is None:
		return get_all_series_data(series_name)

if __name__ == "__main__":
	import sys
	try:
		series_name = sys.argv[1]
	except:
		print("No series name provided! Aborting...")
		exit()
	try:
		season = int(sys.argv[2])
	except:
		season = None
	try:
		episode_number = int(sys.argv[3])
	except:
		episode_number = None
	print(lookup_series(series_name, season, episode_number))
