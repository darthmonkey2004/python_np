import os
import tmdbsimple as tmdb
import keyring
from np.core.conf import readConf
conf = readConf()

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
		print("Error storing api key in keyring:{e}")
		return None

def get_api_key():
	try:
		api_key = keyring.get_password(service_name='tmdb_api', username=os.getlogin())
	except:
		api_key = store_api_key()
	return api_key

def query_movies(title, year=None):
	tmdb.API_KEY = get_api_key()
	if tmdb.API_KEY is None:
		tmdb.API_KEY = store_api_key()
	print("api key:", tmdb.API_KEY)
	data = tmdb.Search().movie(query=title, year=year)['results'][0]
	info = {}
	info['title'] = title
	for k in data.keys():
		if k == 'id':
			info['tmdbid'] = data['id']
		elif k == 'release_date':
			info['year'] = int(data['release_date'].split('-')[0])
			info['release_date'] = data['release_date']
		elif k == 'overview':
			info['description'] = data[k]
		if 'path' in k:
			if k == 'poster_path':
				info['poster'] = f"https://image.tmdb.org/t/p/original{data[k]}"
			else:
				info[k] = f"https://image.tmdb.org/t/p/original{data[k]}"
	info['results'] = True
	info['duration'] = 'None'
	return info

if __name__ == "__main__":
	import sys
	try:
		title = sys.argv[1]
	except:
		print("No title provided! Aborting...")
		exit()
	try:
		year = int(sys.argv[2])
	except:
		year = None
	print(query_movies(title, year))
