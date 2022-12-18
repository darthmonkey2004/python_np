import subprocess

def dump(table):
	dbfile = '/home/monkey/.np/nplayer.db'
	temp_sql = f"/home/monkey/.np/{table}.backup.sql"
	return subprocess.check_output(f"sqlite3 \"{dbfile}\" \".dump {table}\" > \"{temp_sql}\"", shell=True).decode().strip()

def restore(table):
	dbfile = '/home/monkey/.np/nplayer.db'
	temp_sql = f"/home/monkey/.np/{table}.backup.sql"
	subprocess.check_output(f"sqlite3 \"{dbfile}\" \"drop {table};\"", shell=True).decode().strip()
	subprocess.check_output(f"cat \"{temp_sql}\" | sqlite3 \"{dbfile}\"", shell=True).decode().strip()


def write(table, data):
	j = "\n"
	data = j.join(data)
	temp_sql = f"/home/monkey/.np/{table}.backup.modified.sql"
	with open (temp_sql, 'w') as f:
		f.write(data)
		f.close()
	return

def read_backup(table):
	with open(f"/home/monkey/.np/{table}.backup.sql", 'r') as f:
		data = f.read().split("\n")
		f.close()
	return data



def replace_id(table):
	global unique_id
	out = []
	data = read_backup(table)
	for line in data:
		if 'PRAGMA' in line or 'BEGIN TRANSACTION;' in line or 'CREATE TABLE' in line or 'COMMIT;' in line:
			out.append(line)
			pass
		else:
			unique_id += 1
			print(unique_id)
			s = f"INSERT INTO {table} VALUES("
			try:
				_id = line.split(f"INSERT INTO {table} VALUES(")[1].split(',')[0]
				s = f"{s}{_id},"
				remainder = line.split(s)[1]
				j = f"INSERT INTO {table} VALUES({unique_id},"
				line = f"{j}{remainder}"
				out.append(line)
			except:
				out.append(line)
				break
	write(table, out)




if __name__ == "__main__":
	unique_id = 0
	dump('movies')
	dump('series')
	dump('music')
	replace_id('series')
	replace_id('movies')
	replace_id('music')
	restore('series')
	restore('movies')
	restore('music')
