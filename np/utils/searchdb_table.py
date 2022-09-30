import subprocess
from np import create_media, get_columns

def sqlite3(query):
	dbfile = (f"/home/monkey/.np/nplayer.db")
	com = (f"sqlite3 '{dbfile}' \"{query}\"")
	r = subprocess.check_output(com, shell=True).decode().strip().lower().split("\n")
	out = []
	for items in r:
		temp = []
		for chunk in items.split('|'):
			temp.append(chunk)
		t = tuple(temp)
	out.append(t)
	return out


def search_table(table, query_string):
	pragma = get_columns(table)
	rows = None
	if table == 'series':
		if ':' in query_string:
			qstring = []
			queries = query_string.split(':')
			i = -1
			for q in queries:
				i += 1
				string = None
				if i == 0:
					string = f"series_name like '%{q}%'"
				elif i == 1:
					string = f"season = {q}"
				elif i == 2:
					string = f"episode_number = {q}"
				if string is not None:
					qstring.append(string)
			j = " and "
			query_string = j.join(qstring)
		com = f"select id, series_name, tmdbid, season, episode_number, episode_name, description, air_date, still_path, filepath from series where {query_string} order by series_name, season, episode_number;"
		rows = sqlite3(com)
		if rows is not None:
			media = create_media(play_type=table, rows=rows)
		return media
	elif table == 'movies':
		if ':' in query_string:
			qstring = []
			queries = query_string.split(':')
			i = -1
			for q in queries:
				i += 1
				string = None
				if i == 0:
					string = f"title like '%{q}%'"
				elif i == 1:
					string = f"year like '%{q}%'"
				elif i == 2:
					string = f"filepath like '%{q}%'"
				if string is not None:
					qstring.append(string)
			j = " and "
			query_string = j.join(qstring)
		else:
			query_string = (f"title like '%{query_string}%'")
		rows = sqlite3(f"select id, tmdbid, title, year, release_date, description, poster, filepath from movies where {query_string} order by title;")
		if rows is not None:
			media = create_media(rows=rows)
		return media
	elif table == 'music':
		pass
