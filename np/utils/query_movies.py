import urllib
import requests
import json
from np import log
import time

#TODO: create fail logger, or find switchover solution when 100 tmdb api calls daily is exhausted.



def set_empty(title):
	info = {}
	info['title'] = title
	info['isactive'] = 1
	info['tmdbid'] = 'Unknown'
	info['release_date'] = 'Unknown'
	info['duration'] = 0
	info['filepath'] = None
	info['md5'] = None
	info['url'] = None
	info['description'] = 'Unknown'
	info['year'] = 'Unknown'
	info['poster'] = 'Unknown'
	return info



def query_imdb(title):
	attempts = 0
	log (f"Looking up movie... Title: '{title}'", 'info')
	info = {}
	title_nw = urllib.parse.quote(title)
	tmdb_api_key = "ac1bdc4046a5e71ef8aa0d0bd93f8e9b"
	imdb_api_key = "k_6lkh4g0z"
	tmdb_url = ("https://api.themoviedb.org/3/search/movie?api_key=" + str(tmdb_api_key) + "&language=en-US&query=" + title_nw + "page=1&include_adult=false")
	imdb_url = ("https://imdb-api.com/en/API/SearchMovie/" + str(imdb_api_key) + "/" + title_nw)
	r = requests.get(imdb_url)
	if r.status_code != 200:
		out = (f"TMDB Query Error: Response code {r.status_code}")
		log(out, 'error')
		info = set_empty(title)
		return info
	json_data = json.loads(r.text)
	errmsg = json_data['errorMessage']
	if errmsg is not None:
		tries_exceeded = 'Maximum usage'
		if errmsg == 'Server busy':
			attempts += 1
			while attempts < 4:
				log(f"TMDB query: Server Busy. Retrying in 5 seconds... (Attempts: {attempts} of 3)", 'info')
				time.sleep(5)
				r = requests.get(imdb_url)
				if r.status_code == 200:
					json_data = json.loads(r.text)
					errmsg = json_data['errorMessage']
					if errmsg is None:
						break
			log (f"TMDB lookup failed! Server is busy, maximum attempts exceeded", 'error')
			info = set_empty(title)
			return info
		if tries_exceeded in errmsg:
			log (f"Uh, oh! Out of lookups for today! Aborting...", 'error')
			info = set_empty(title)
			return info
	if json_data['results'] is None:
		log (f"Failed to get results for title: '{title}'!", 'error')
		info = set_empty(title)
		return info


				
				
	imdbid = json_data['results'][0]['id']
	imdb_url2 = ("https://www.imdb.com/title/" + str(imdbid) + "/plotsummary?ref_=tttg_sa_1")
	r = requests.get(imdb_url2)
	if r.status_code != 200:
		out = ("Error:", r.status_code)
		return out
	s = '<li class="ipl-zebra-list__item" id="summary-'
	try:
		data = r.text.split(s)[1]
	except Exception as e:
		log (f"query_movies.py, query_imdb exception: {e}", 'error')
		return None
	info['description'] = data.split('</p>')[0].split('<p>')[1]
	data = r.text.split("\n")
	pos = -1
	for line in data:
		pos = pos + 1
		if 'class="poster"' in line:
			poster_pos = pos + 4
			info['poster'] = data[poster_pos].split('"')[1]
		elif ') - Plot Summary Poster"' in line:
			info['title'] = line.split('"')[1].split('(')[0].strip()
			info['year'] = line.split('"')[1].split('(')[1].split(')')[0]			
			if ' ' in str(info['year']):
				chunks = info['year'].split(' ')
				for chunk in chunks:
					try:
						chunk = int(chunk)
						if chunk >= 0:
							info['year'] = chunk
							break
					except:
						pass
	info['isactive'] = 1
	try:
		info['tmdbid'] = imdbid
	except:
		info['tmdbid'] = 'None'
	try:
		info['release_date'] = info['year']
	except:
		info['release_data'] = 'Unknown'
	
	info['duration'] = 0
	info['filepath'] = None
	info['md5'] = None
	info['url'] = None
	return info

if __name__ == "__main__":
	import sys
	try:
		title = sys.argv[1]
	except:
		print ("no title provided!")
		exit()
	info = query_imdb(title)
	#print (info)
