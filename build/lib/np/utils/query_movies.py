import urllib
import requests
import json

def query_imdb(title):
	info = {}
	title_nw = urllib.parse.quote(title)
	tmdb_api_key = "ac1bdc4046a5e71ef8aa0d0bd93f8e9b"
	imdb_api_key = "k_6lkh4g0z"
	tmdb_url = ("https://api.themoviedb.org/3/search/movie?api_key=" + str(tmdb_api_key) + "&language=en-US&query=" + title_nw + "page=1&include_adult=false")
	imdb_url = ("https://imdb-api.com/en/API/SearchMovie/" + str(imdb_api_key) + "/" + title_nw)
	r = requests.get(imdb_url)
	if r.status_code != 200:
		out = ("Error:", r.status_code)
		return out
	json_data = json.loads(r.text)
	imdbid = json_data['results'][0]['id']

	imdb_url2 = ("https://www.imdb.com/title/" + str(imdbid) + "/plotsummary?ref_=tttg_sa_1")
	r = requests.get(imdb_url2)
	if r.status_code != 200:
		out = ("Error:", r.status_code)
		return out
	s = '<li class="ipl-zebra-list__item" id="summary-'
	data = r.text.split(s)[1]
	info['description'] = data.split('</p>')[0].split('<p>')[1]
	data = r.text.split("\n")
	pos = -1
	for line in data:
		pos = pos + 1
		if 'class="poster"' in line:
			poster_pos = pos + 4
			info['poster'] = data[poster_pos].split('"')[1]
			print (info['poster'])
		elif ') - Plot Summary Poster"' in line:
			info['title'] = line.split('"')[1].split('(')[0].strip()
			info['year'] = line.split('"')[1].split('(')[1].split(')')[0]
				
	info['isactive'] = 1
	info['tmdbid'] = imdbid
	info['release_date'] = info['year']
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
	print (info)
