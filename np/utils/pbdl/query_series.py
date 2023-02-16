import os
import tmdbsimple as tmdb
from np.core.conf import readConf
import keyring
import getpass

def store_api_key(api_key=None):
	try:
		conf = readConf()
		if api_key is None:
			api_key = conf['tmdb_api_key']
	except Exception as e:
		print("API Key not set!", e)
		return None
	service_name = 'tmdb_api'
	user = os.getlogin()
	try:
		keyring.set_password(service_name=service_name, username=user, password=api_key)
		return api_key
	except Exception as e:
		print(f"Error storing api key in keyring:{e}")
		return None

def get_api_key():
	try:
		api_key = keyring.get_password(service_name='tmdb_api', username=os.getlogin())
	except:
		api_key = store_api_key()
	return api_key

def get_series_id(series_name):
	tmdb.API_KEY = get_api_key()
	if tmdb.API_KEY is None:
		conf = readConf()
		tmdb.API_KEY = conf['tmdb_api_key']
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
	info['season'] = season
	for k in s.keys():
		if k == 'episodes':
			info['episodes'] = {}
			for item in s[k]:
				episode_number = int(item['episode_number'])
				info['episodes'][episode_number] = {}
				info['episodes'][episode_number]['air_date'] = item['air_date']
				info['episodes'][episode_number]['unique_id'] = item['id']
				info['episodes'][episode_number]['episode_name'] = item['name']
				info['episodes'][episode_number]['description'] = item['overview']
				info['episodes'][episode_number]['season'] = item['season_number']
				info['episodes'][episode_number]['still_path'] = f"https://image.tmdb.org/t/p/original{item['still_path']}"
				info['episodes'][episode_number]['guest_stars'] = item['guest_stars']
				info['episodes'][episode_number]['tmdbid'] = _id
				info['episodes'][episode_number]['isactive'] = 1
				info['episodes'][episode_number]['season'] = season
				info['episodes'][episode_number]['episode_number'] = episode_number
		elif 'path' in k:
			info[k] = f"https://image.tmdb.org/t/p/original{s[k]}"
		else:
			info[k] = s[k]
	if series_name is not None:
		info['series_name'] = series_name
	return info

def get_episode_data(_id, season, episode_number):
	season = int(season)
	episode_number = int(episode_number)
	if type(_id) == str:
		series_name = str(_id)
		_id = int(get_series_id(series_name))
	else:
		series_name = None
	info = get_season_data(_id, season)
	out = info[season]['episodes'][episode_number]
	out['results'] = True
	out['id'] = _id
	out['series_name'] = series_name
	return out

def get_all_series_data(query='Disenchantment'):
	_id = get_series_id(query)
	seasons = get_seasons(_id)
	info = {}
	info[query] = {}
	info[query]['series_name'] = query
	info[query]['id'] = _id
	info[query]['seasons'] = get_seasons(_id)
	for season in info[query]['seasons'].keys():
		info[query]['seasons'][season] = get_season_data(_id, season)
	return info


def query_series(series_name, season=None, episode_number=None):
	tmdb.API_KEY = get_api_key()
	if tmdb.API_KEY is None:
		conf = readConf()
		tmdb.API_KEY = conf['tmdb_api_key']
	print("querying series:", series_name)
	if season is not None and episode_number is not None:
		info = get_episode_data(series_name, season, episode_number)
	elif season is not None and episode_number is None:
		info = get_season_data(series_name, season)
	elif season is None and episode_number is None:
		info = get_all_series_data(series_name)
	info['series_name'] = series_name
	return info

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
