import traceback, sys
import urllib
import requests
import json
from np.core.log import np_logger
logger = np_logger().log_msg
import time
from np.core.nplayer_db import get_columns
from np.utils.pbdl.utils import set_api_key_tmdb
from np.core.conf import readConf
conf = readConf()
try:
	haskeys = conf['api_keys']
	API_KEY = conf['api_keys']['TMDB']
except:
	API_KEY = set_api_key_tmdb()

def log(msg, _type=None):
	if _type is None:
		_type = 'info'
	if _type == 'error':
		exc_info = sys.exc_info()
		logger(msg, _type, exc_info)
		return
	else:
		logger(msg, _type)



def set_empty():
	pragma = get_columns('movies')
	columns = list(pragma.keys())
	info = {}
	for key in columns:
		dtype = pragma[key]['data_type']
		if dtype == 'INTEGER' or dtype == 'BOOL':
			info[key] = 0
		elif dtype == 'TEXT':
			info[key] = 'Unknown'
	info['results'] = False
	return info



def query_movies(title):
	info = set_empty()
	info['title'] = title
	attempts = 0
	log (f"Looking up movie... Title: '{title}'", 'info')
	title_nw = urllib.parse.quote(title)
	global API_KEY
	tmdb_url = (f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&language=en-US&query={title_nw}&page=1&include_adult=false")
	r = requests.get(tmdb_url)
	if r.status_code != 200:
		log(f"TMDB Query Error: Response code {r.status_code}", 'error')
		return info
	try:
		json_data = json.loads(r.text)
		errmsg = None
		if type == 'tmdb':
			data = json_data['results'][0]
			info['title'] = data['title']
			info['year'] = data['release_date'].split('-')[0]
			info['tmdbid'] = data['id']
			info['description'] = data['overview']
			info['poster'] = data['poster_path']
			info['results'] = True
			return info


	except Exception as e:
		log("Error: {e}", 'error')
		return info


if __name__ == "__main__":
	import sys
	try:
		title = sys.argv[1]
	except:
		print ("no title provided!")
		exit()
	info = query_imdb(title)
	print (info)
