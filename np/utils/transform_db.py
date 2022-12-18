import subprocess
import os

def sqlite3(com):
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	com = f"sqlite3 \"{dbfile}\" \"{com}\""
	try:
		return subprocess.check_output(com, shell=True).decode().strip()
	except:
		return None

def get_tables():
	data = sqlite3(".tables")
	tables = []
	for item in data.split('  '):
		tables.append(item.strip())
	return tables



def get_schema(table):
	data = sqlite3(f".schema {table}").split('(')[1].split(')')[0].split(', ')
	d = {}
	for line in data:
		if 'PRIMARY' in line:
			primary = True
		else:
			primary = False
		if 'NOT NULL' in line:
			required = True
		else:
			required = False
		if 'INTEGER' in line:
			s = 'INTEGER'
		elif 'BOOL' in line:
			s = 'BOOL'
		elif 'TEXT' in line:
			s = 'TEXT'
		key = line.split(s)[0]
		d[key] = {}
		d[key]['is_primary'] = primary
		d[key]['is_required'] = required
		d[key]['dtype'] = s
	return d

def dump():
	unique_id = 0
	tables = get_tables()
	d = {}
	d['create'] = {}
	d['schema'] = {}
	d['data'] = {}
	header1 = "PRAGMA foreign_keys=OFF;"
	header2 = "BEGIN TRANSACTION;"
	footer = "COMMIT;"
	d['create']['movies'] = "CREATE TABLE movies (id INTEGER PRIMARY KEY AUTOINCREMENT, isactive BOOL, tmdbid INTEGER, title TEXT, year INTEGER, release_date TEXT, duration TEXT, description TEXT, poster TEXT, filepath TEXT NOT NULL);"
	d['create']['series'] = "CREATE TABLE series (id INTEGER PRIMARY KEY AUTOINCREMENT, isactive BOOL, series_name TEXT NOT NULL, tmdbid INTEGER, season INTEGER, episode_number INTEGER, episode_name TEXT, description TEXT, air_date TEXT, still_path TEXT, filepath TEXT NOT NULL);"
	d['create']['music'] = "CREATE TABLE music (id INTEGER PRIMARY KEY AUTOINCREMENT, isactive BOOL, title TEXT, mbid TEXT, album TEXT, album_id TEXT, artist_id TEXT, artist TEXT, genre TEXT, track INT, filepath TEXT NOT NULL, poster TEXT);"
	d['schema']['movies'] = get_schema('movies')
	d['schema']['series'] = get_schema('series')
	d['schema']['music'] = get_schema('music')
	ct = {}
	ct_movies = int(sqlite3(f"select Count(*) from movies;"))
	ct_music = int(sqlite3(f"select Count(*) from music;"))
	ct_series = int(sqlite3(f"select Count(*) from series;"))
	total = ct_movies + ct_music + ct_series
	for table in tables:	
		columns = list(d['schema'][table].keys())
		data = sqlite3(f"select * from {table};").split("\n")
		for line in data:
			unique_id += 1
			print(f"progress: {unique_id} / {total}")
			d['data'][table][unique_id] = {}
			if header1 not in line and header2 not in line and footer not in line and d['create'][table] not in line:
				vals = line.split('|')
				pos = -1
				for val in vals:
					pos += 1
					try:
						column = columns[pos]
						dtype = d['schema'][table][column]['dtype']
						if val == "'null'" or val == 'null' or val == 'NULL' or val == '' or val == 'Unknown':
							val = None
						if dtype == 'INTEGER':
							if val is None:
								val = 0
							d['data'][table][unique_id][column] = int(val)
						elif dtype == 'BOOL':
							if val is None:
								val = 0
							d['data'][table][unique_id][column] = bool(val)
						elif dtype == 'TEXT':
							if val is None:
								val = 'null'
							d['data'][table][unique_id][column] = str(val)
					except Exception as e:
						print(f"line:{line}")
						print("done???", e)
					d['data'][table][unique_id]['id'] = unique_id
	return d


if __name__ == "__main__":
	data = dump()
	for table in data['data'].keys():
		newdata = []
		filepath = f"{table}.sql"
		header1 = "PRAGMA foreign_keys=OFF;\n"
		header2 = "BEGIN TRANSACTION;\n"
		footer = "COMMIT;\n"
		create = data['create'][table]
		opener = f"{header1}{header2}{create}\n"
		with open(filepath, 'a') as f:
			f.write(opener)
			f.close()
		
	
