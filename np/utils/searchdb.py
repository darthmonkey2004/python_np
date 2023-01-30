from np.core.log import np_logger
import os
import subprocess

log = np_logger().log_msg

def sqlite3(query):
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	com = f"sqlite3 \"{dbfile}\" \"{query}\""
	try:
		ret = subprocess.check_output(com, shell=True).decode().strip().replace('|', ':')
		if ret != '':
			if '::' in ret:
				ret = ret.replace('::', ':None:')
			if "\n" in ret:
				ret = ret.split("\n")
			return ret
		else:
			return None
	except Exception as e:
		#log(f"Error: sqlite3 command failed! {e}", 'error')
		return None

def search_music(query_string):
	results = []
	for query in query_string.split(':'):
		if query == '*':
			query = "select artist,title,album,id from music;"
			ret = sqlite3(query)
			if type(ret) == str:
				results.append(ret)
			elif type(ret) == list:
				for item in ret:
					results.append(item)
		else:
			qtitle = f"select artist,title,album,id from music where title like '%{query}%';"
			title = sqlite3(qtitle)
			if title and title not in results:
				if type(title) == str:
					results.append(title)
				elif type(title) == list:
					for item in title:
						results.append(item)
			qartist = f"select artist,title,album,id from music where artist like '%{query}%';"
			artist = sqlite3(qartist)
			if artist and artist not in results:
				if type(artist) == str:
					results.append(artist)
				elif type(artist) == list:
					for item in artist:
						results.append(item)
			qalbum = f"select artist,title,album,id from music where album like '%{query}%';"
			album = sqlite3(qalbum)
			if album and album not in results:
				if type(album) == str:
					results.append(album)
				elif type(album) == list:
					for item in album:
						results.append(item)
			qfilepath = f"select artist,title,album,id from music where filepath like '%{query}%';"
			filepath = sqlite3(qfilepath)
			if filepath and filepath not in results:
				if type(filepath) == str:
					results.append(filepath)
				elif type(filepath) == list:
					for item in filepath:
						results.append(item)
	ret = []
	for item in results:
		ret.append(f"music:{item}")
	return ret


def search_movies(query_string):
	results = []
	if query_string == '*':
		query = "select title,year,id from movies;"
		ret = sqlite3(query)
		if type(ret) == str:
			results.append(ret)
		elif type(ret) == list:
			for item in ret:
				results.append(item)
	else:
		for query in query_string.split(':'):
			qtitle = f"select title,year,id from movies where title like '%{query}%';"
			title = sqlite3(qtitle)
			if title and title not in results:
				if type(title) == str:
					results.append(title)
				elif type(title) == list:
					for item in title:
						results.append(item)
			qfilepath = f"select title,year,id from movies where filepath like '%{query}%';"
			filepath = sqlite3(qfilepath)
			if filepath and filepath not in results:
				if type(filepath) == str:
					results.append(filepath)
				elif type(filepath) == list:
					for item in filepath:
						results.append(item)
	ret = []
	for item in results:
		ret.append(f"movies:{item}")
	return ret

def search_series(query_string):
	if query_string == '*':
		results = []
		query = f"select series_name,season,episode_number,episode_name,id from series order by series_name,season,episode_number;"
		ret = sqlite3(query)
		print(type(ret), ret)
		if type(ret) == str:
			results.append(f"series:{ret}")
		elif type(ret) == list:
			for item in ret:
				results.append(f"series:{item}")
		return results
	else:
		query = query_string.split(':')
		series_name = query[0]
		try:
			season = query[1]
		except:
			season = None
		try:
			episode_number = query[2]
		except:
			episode_number = None
		if episode_number is None and season is None and series_name is not None:
			qstring = f"select series_name,season,episode_number,episode_name,id from series where series_name like '%{series_name}%' order by series_name,season,episode_number;"
		elif episode_number is None and season is not None and series_name is not None:
			qstring = f"select series_name,season,episode_number,episode_name,id from series where series_name like '%{series_name}%' and season = {season} order by series_name,season,episode_number;"
		elif episode_number is not None and season is not None and series_name is not None:
			qstring = f"select series_name,season,episode_number,episode_name,id from series where series_name like '%{series_name}%' and season = {season} and episode_number = {episode_number} order by series_name,season,episode_number;"
		ret = sqlite3(qstring)
		if ret is not None:
			if type(ret) == str:
				ret = ret.split("\n")
		else:
			ret = []
		results = []
		for item in ret:
			results.append(f"series:{item}")
		return results


def querydb(tables, query):
	ret = []
	if type(tables) != list:
		if "," in tables:
			tables = tables.split(",")
		else:
			tables = [tables]
	for table in tables:
		print("table:", table)
		if table == 'series':
			ret = search_series(query)
		elif table == 'movies':
			ret = search_movies(query)
		elif table == 'music':
			for item in search_music(query):
				if item not in ret:
					ret.append(item)
		elif table == 'all':
			results = search_series(query)
			if results:
				for item in results:
					if item not in ret:
						ret.append(item)
			results = search_movies(query)
			if results:
				for item in results:
					if item not in ret:
						ret.append(item)
			results = search_music(query)
			if results:
				for item in results:
					if item not in ret:
						ret.append(item)
	return ret

if __name__ == "__main__":
	import sys
	try:
		table = sys.argv[1]
	except:
		table = 'movies'
	try:
		query = sys.argv[2]
	except:
		query = 'Chappie'
	ret = querydb(table, query)
	print(ret)
