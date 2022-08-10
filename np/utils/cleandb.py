import subprocess
from np import log
import os
import datetime
home = os.path.expanduser("~")
DATA_DIR = (home + os.path.sep + ".np")


def run_shell(com):
	out = subprocess.check_output(com, shell=True).decode()
	if out:
		print(out)
		return out
	else:
		return True

def backup_db():
	print ("Backing up...")
	ts = datetime.datetime.now().timestamp()
	movies_sql = (f"{DATA_DIR}{os.path.sep}movies.sql")
	series_sql = (f"{DATA_DIR}{os.path.sep}series.sql")
	music_sql = (f"{DATA_DIR}{os.path.sep}music.sql")
	if os.path.exists(movies_sql):
		print ("Movies.sql")
		new_sql = (f"{movies_sql}.{ts}.backup.sql")
		com = (f"mv '{movies_sql}' '{new_sql}'")
		ret = run_shell(com)
		if ret is not True:
			print (f"Error: {ret}")
			input()
	if os.path.exists(series_sql):
		print ("Series.sql")
		new_sql = (f"{series_sql}.{ts}.backup.sql")
		com = (f"mv '{series_sql}' '{new_sql}'")
		ret = run_shell(com)
		if ret is not True:
			print (f"Error: {ret}")
			input()
	if os.path.exists(music_sql):
		print ("Music.sql")
		new_sql = (f"{music_sql}.{ts}.backup.sql")
		com = (f"mv '{music_sql}' '{new_sql}'")
		ret = run_shell(com)
		if ret is not True:
			print (f"Error: {ret}")
			input()
	print ("dumping movies..")
	com = (f"cd '{DATA_DIR}'; sqlite3 nplayer.db '.dump movies' > movies.sql")
	ret = run_shell(com)
	if ret is not True:
		print (f"Error: {ret}")
		input()
	print ("dumping series...")
	com = (f"cd '{DATA_DIR}'; sqlite3 nplayer.db '.dump series' > series.sql")
	ret = run_shell(com)
	if ret is not True:
		print (f"Error: {ret}")
		input()
	print ("dumping music...")
	com = (f"cd '{DATA_DIR}'; sqlite3 nplayer.db '.dump music' > music.sql")
	ret = run_shell(com)
	if ret is not True:
		print (f"Error: {ret}")
		input()

def remove_items(_list, table):
	print (f"removing from {table}...")
	pos = 0
	dbfile = (f"{DATA_DIR}{os.path.sep}nplayer.db")
	for _id in _list:
		pos += 1
		print (f"Removing id: {_id}. Progress: {pos}/{len(_list)}")
		com = (f"sqlite3 '{dbfile}' 'delete from {table} where id = {_id};'")
		ret = subprocess.check_output(com, shell=True).decode()
		if ret is not True and ret != '':
			log(f"cleandb.py: Error encountered in removal. ID: {_id}, Data: '{ret}'", 'error')
	return True

def clean_movies():
	print ("Scanning movies for duplicates..")
	com = (f"cd '/home/monkey/.np'; sqlite3 nplayer.db 'select title,id from movies order by title;'")
	_list = subprocess.check_output(com, shell=True).decode().strip().split('\n')
	keep = []
	trash = []
	for item in _list:
		chunks = item.split('|')
		title = chunks[0]
		_id = chunks[1]
		if title not in keep:
			keep.append(title)
		elif title in keep:
			trash.append(_id)
	print (f"Found {len(trash)} duplicate entries.")
	remove_items(trash, 'movies')
	print ("Done!")

def clean_series():
	print ("Scanning series for duplicates..")
	com = (f"cd '/home/monkey/.np'; sqlite3 nplayer.db 'select series_name,season,episode_number,id from series order by series_name,season,episode_number;'")
	_list = subprocess.check_output(com, shell=True).decode().strip().split('\n')
	keep = []
	trash = []
	for item in _list:
		chunks = item.split('|')
		series_name = chunks[0]
		season = chunks[1]
		episode_number = chunks[2]
		string = (f"{series_name}|{season}|{episode_number}")
		_id = chunks[3]
		if string not in keep:
			keep.append(string)
		elif string in keep:
			trash.append(_id)
			print (f"Duplicate:{string}")
	print (f"Found {len(trash)} duplicate entries.")
	input()
	remove_items(trash, 'series')
	print ("Done!")

def run():
	backup_db()
	clean_movies()
	clean_series()


if __name__ == "__main__":
	run()
