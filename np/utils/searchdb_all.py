from np.core.core import create_media
import re
import subprocess


def sqlite3(query):
	dbfile = (f"/home/monkey/.np/nplayer.db")
	com = (f"sqlite3 '{dbfile}' \"{query}\"")
	return subprocess.check_output(com, shell=True).decode().strip().lower().split("\n")


def searchdb(query='Three to Tango'):
	all_results = []
	query = query.lower()
	r = re.compile(f".*{query}*")
	series = sqlite3(f"select id, series_name, tmdbid, season, episode_number, episode_name, description, air_date, still_path, filepath from series order by series_name, season, episode_number;")
	results = list(filter(r.match, series))
	if results != []:
		for result in results:
			out = f"series:{result}"
			all_results.append(out)
	movies = sqlite3(f"select id, tmdbid, title, year, release_date, description, poster, filepath from movies order by title;")
	results = list(filter(r.match, movies))
	if results != []:
		for result in results:
			out = f"series:{result}"
			all_results.append(out)
	music = sqlite3(f"select id, title, artist, album from music order by artist,title,album;")
	results = list(filter(r.match, movies))
	if results != []:
		for result in results:
			out = f"series:{result}"
			all_results.append(out)
	return all_results


def refine_search(query, _list):
	r = re.compile(f".*{query}*")
	out = list(filter(r.match, _list))
	return out


def search_all(query):
	out = []
	# get primary search query
	queries = query.split(':')
	q = queries.pop(0)
	# ger initial search results
	results = searchdb(q)
	play_type = None
	for q in queries:
		q = q.lower()
		for result in results:
			if q in result:
				play_type = result.split(':')[0]
				result = result.split(f"{play_type}:")[1]
				result = tuple(result.split('|'))
				out.append(result)
	return create_media(play_type, out)

