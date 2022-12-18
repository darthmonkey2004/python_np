import tmdbsimple as tmdb
tmdb.API_KEY = 'ac1bdc4046a5e71ef8aa0d0bd93f8e9b'

def query_movies(title, year=None):
	data = tmdb.Search().movie(query=title, year=year)['results'][0]
	info = {}
	info[title] = {}
	info[title]['title'] = title
	for k in data.keys():
		if 'path' in k:
			if k == 'poster_path':
				info[title]['poster'] = f"https://image.tmdb.org/t/p/original{data[k]}"
			else:
				info[title][k] = f"https://image.tmdb.org/t/p/original{data[k]}"
		elif k == 'overview':
			info[title]['description'] = data[k]
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
