import sqlite3
from collections import OrderedDict

def create_connection(database=None):
	if database == None:
		database = "/home/monkey/.np/nplayer.db"
	cur = None
	#print ("Using database:", database)
	conn = sqlite3.connect(database)
	return conn


def updatedb(table, update_string, query):
	conn = create_connection()
	cur = conn.cursor()
	# build query string from provided arguments
	query_string = ("UPDATE " + str(table) + " SET " + str(update_string) + " WHERE " + str(query) + ";")
	ret = None
	try:
		ret = cur.execute(query_string)
		if ret:
			return ret
		else:
			conn.commit()
			return None
	except Exception as e:
		return False, e


def addtodb(table, sql_data):
	print ("adding to db:", sql_data)
	try:
		conn = create_connection()
		cur = conn.cursor()
		ret = cur.execute(sql_data)
		conn.commit()
		return True
	except Exception as e:
		print (e)
		return False


def addtodb_new(table=None, data={}):
	try:
		conn = create_connection()
		cur = conn.cursor()
	except Exception as e:
		print ("Unable to create connection or cursor:", e)
		return False
	if table == None:
		print ("No table name provided.")
		return False
	pragma = get_columns(table)
	columns = list(pragma.keys())
	keys = list(data.keys())
	vals = list(data.values())
	query_vars = []
	query_vals = []
	items = OrderedDict()
	pos = -1
	for item in columns:
		if item not in keys:
			items[item] = 'Null'
		else:
			pos = pos + 1
			items[item] = data[item]
	for key in list(items.keys()):
		dtype = pragma[key]['data_type']
		val = items[key]
		if val is None or val == 'None':
			val = 'Null'
		if val != 'Null':
			if dtype == 'INT':
				#try:
				#print ("integer conv:", val, type(val))
				if type(val) == tuple:
					if val != (None, None):
						val = int(str(val[0]))
					else:
						val = 0
				else:
					val = int(str(val))
				query_vars.append(key)
				query_vals.append(str(val))
				#except:
				#	print ("Error: not an integer", vals[pos])
				#	return False
			if dtype == 'TEXT':
				val = ("'" + str(val) + "'")
				query_vals.append(val)
				query_vars.append(key)
			if dtype == 'BOOL':
				try:
					val = bool(val)
					if val:
						val = '1'
					else:
						val = '0'
					query_vals.append(val)
					query_vars.append(key)
				except:
					print ("Unable to convert to boolean:", val)
					return False
		else:
			query_vals.append(val)
			query_vars.append(key)				
	j = ', '
	query_vars = j.join(query_vars)
	query_vals = j.join(query_vals)
	string = ("INSERT INTO " + str(table) + "(" + query_vars + ") VALUES(" + query_vals + ");")
	try:
		cur.execute(string)
		conn.commit()
		return True
	except Exception as e:
		("Failed to add data:", e)
		return False


def removefromdb(table, sql_query):
	print ("Removing from db:", table, sql_query)
	try:
		conn = create_connection()
		cur = conn.cursor()
		query_string = ("delete from " + str(table) + " where " + str(sql_query) + ";")
		cur.execute(query_string)
		ret = conn.commit()
		if ret:
			print (ret)
			return False
		else:
			return True
	except Exception as e:
		print (e)
		return False

def querydb(table, column='*', query=None):
	conn = create_connection()
	cur = conn.cursor()
	# build query string from provided arguments
	if query == None:
		if table == 'series':
			query_string = ("SELECT " + column + " from " + str(table) + " order by series_name,season,episode_number;")
		elif table == 'movies':
			query_string = ("SELECT " + column + " from " + str(table) + " order by title;")
		elif table == 'music':
			query_string = ("SELECT " + column + " from " + str(table) + " order by artist,track;")
		else:
			print ("Unknown table:", table)
			rows = []
	else:
		if table == 'series':
			query_string = ("SELECT " + column + " from " + str(table) + " WHERE " + str(query) + " order by series_name,season,episode_number;")
		elif table == 'movies':
			query_string = ("SELECT " + column + " from " + str(table) + " WHERE " + str(query) + " order by title;")
		elif table == 'music':
			query_string = ("SELECT " + column + " from " + str(table) + " WHERE " + str(query) + " order by artist,track;")
		else:
			print ("Unknown table:", table)
			rows = []
	try:
		cur.execute(query_string)
		rows = cur.fetchall()
	except Exception as e:
		print (e)
		rows = []
	return rows


def create_table_series():
	conn = create_connection()
	cur = conn.cursor()
	sql = "CREATE TABLE IF NOT EXISTS series (id INTEGER PRIMARY KEY AUTOINCREMENT, isactive BOOL, series_name TEXT NOT NULL, tmdbid INTEGER, season INTEGER, episode_number INTEGER, episode_name TEXT, description TEXT, air_date TEXT, still_path TEXT, filepath TEXT NOT NULL);"
	cur.execute(sql)
	conn.commit()
	

def create_table_movies():
	conn = create_connection()
	cur = conn.cursor()
	sql = "CREATE TABLE IF NOT EXISTS movies (id INTEGER PRIMARY KEY AUTOINCREMENT, isactive BOOL, tmdbid INTEGER, title TEXT, year INTEGER, release_date TEXT, duration TEXT, description TEXT, poster TEXT, filepath TEXT NOT NULL);"
	cur.execute(sql)
	conn.commit()


def create_table_music():
	conn = create_connection()
	cur = conn.cursor()
	sql = "CREATE TABLE IF NOT EXISTS music (id INTEGER PRIMARY KEY AUTOINCREMENT, isactive BOOL, title TEXT, accoustic_id TEXT, album TEXT, album_id TEXT, artist_id TEXT, year INT, artist TEXT, track INT, track_ct INT, filepath TEXT NOT NULL);"
	cur.execute(sql)
	conn.commit()


def create_db(table=None):
	try:
		if table == None:
			create_table_series()
			create_table_movies()
			create_table_music()
			return True
		elif table == 'series':
			create_table_series()
			return True
		elif table == 'movies':
			create_table_movies()
			return True
		elif table == 'music':
			create_table_music()
			return True
		else:
			print ("Unknown table:", table)
			return False
	except Exception as e:
		print (e)
		return False

def get_columns(table):
	conn = create_connection()
	cur = conn.cursor()
	# build query string from provided arguments
	query_string = ("PRAGMA table_info(" + table + ");")
	ret = None
	cur.execute(query_string)
	rows = cur.fetchall()
	ct = len(rows)
	columns = {}
	for row in rows:
		row_data = {}
		row_id, column, data_type, is_required, notaclue, is_primary = row
		row_data['row_id'] = row_id
		row_data['data_type'] = data_type
		row_data['is_required'] = is_required
		row_data['is_primary'] = is_primary
		columns[column] = row_data
	return columns

def test_db():
	import subprocess
	com = ('cd "$HOME/.np"; sqlite3 nplayer.db ".schema"')
	ret = subprocess.check_output(com, shell=True).decode()
	if ret == '':
		print("Schema empty! Creating...")
		create_db()
		return
	else:
		return ret
	
