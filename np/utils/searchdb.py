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

def search_music(query_string, getfilepath=False):
	results = []
	for query in query_string.split(':'):
		if query == '*':
			if getfilepath:
				query = "select artist,title,album,id,filepath from music;"
			else:
				query = "select artist,title,album,id from music;"
			ret = sqlite3(query)
			if type(ret) == str:
				results.append(ret)
			elif type(ret) == list:
				for item in ret:
					results.append(item)
		else:
			if getfilepath:
				qtitle = f"select artist,title,album,id,filepath from music where title like '%{query}%';"
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


def search_movies(query_string, getfilepath=False):
	results = []
	if query_string == '*':
		if getfilepath:
			query = "select title,year,id,filepath from movies;"
		else:
			query = "select title,year,id from movies;"
		ret = sqlite3(query)
		if type(ret) == str:
			results.append(ret)
		elif type(ret) == list:
			for item in ret:
				results.append(item)
	else:
		for query in query_string.split(':'):
			if getfilepath:
				qtitle = f"select title, year,id,filepath from movies where title like '%{query}%';"
			else:
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

def search_series(query_string, getfilepath=False):
	if query_string == '*':
		results = []
		query = f"select series_name,season,episode_number,episode_name,id from series order by series_name,season,episode_number;"
		ret = sqlite3(query)
		#print(type(ret), ret)
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
			if '-' in season:
				start = int(season.split('-')[0])
				end = int(season.split('-')[1])
				season = []
				for i in range(start, end+1):
					season.append(i)
			elif "," in season:
				season = season.split(',')
			else:
				season = [season]
		except:
			season = []
		try:
			episode_number = query[2]
			if '-' in episode_number:
				start = int(episode_number.split('-')[0])
				end = int(episode_number.split('-')[1])
				episode_number = []
				for i in range(start, end+1):
					episode_number.append(i)
			elif "," in episode_number:
				episode_number = episode_number.split(',')
			else:
				episode_number = [episode_number]
		except:
			episode_number = []
		q = []
		if len(season) == 0 and len(episode_number) == 0:
			q.append(f"series_name like \'%{series_name}%\'")
		elif len(season) == 0 and len(episode_number) >= 1:
			for e in episode_number:
				q.append(f"series_name like \'%{series_name}%\' and episode_number = {e}")
		elif len(season) >= 1 and len(episode_number) == 0:
			for s in season:
				q.append(f"series_name like \'%{series_name}%\' and season = {s}")
		elif len(season) >= 1 and len(episode_number) >= 1:
			for s in season:
				for e in episode_number:
					q.append(f"series_name like \'%{series_name}%\' and season = {s} and episode_number = {e}")
		query = " or ".join(q)
		if getfilepath:
			qstring = f"select series_name,season,episode_number,episode_name,id,filepath from series where {query} order by series_name,season,episode_number;"
		else:
			qstring = f"select series_name,season,episode_number,episode_name,id from series where {query} order by series_name,season,episode_number;"
		#print("qstring:", qstring)
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


def querydb(tables, query, getfilepath=False):
	ret = []
	if type(tables) != list:
		if "," in tables:
			tables = tables.split(",")
		else:
			tables = [tables]
	for table in tables:
		#print("table:", table)
		if table == 'series':
			ret = search_series(query_string=query, getfilepath=getfilepath)
		elif table == 'movies':
			ret = search_movies(query_string=query, getfilepath=getfilepath)
		elif table == 'music':
			for item in search_music(query_string=query, getfilepath=getfilepath):
				if item not in ret:
					ret.append(item)
		elif table == 'all':
			results = search_series(query)
			if results:
				for item in results:
					if item not in ret:
						ret.append(item)
			results = search_movies(query_string=query, getfilepath=getfilepath)
			if results:
				for item in results:
					if item not in ret:
						ret.append(item)
			results = search_music(query_string=query, getfilepath=getfilepath)
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
