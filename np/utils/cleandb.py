import subprocess
from np.core.log import np_logger
import os
import datetime
log = np_logger().log_msg
home = os.path.expanduser("~")
DATA_DIR = (home + os.path.sep + ".np")


def run_shell(com):
	out = subprocess.check_output(com, shell=True).decode()
	if out:
		return out
	else:
		return True

def backup_db():
	log("Backing up...", 'info')
	ts = datetime.datetime.now().timestamp()
	movies_sql = (f"{DATA_DIR}{os.path.sep}movies.sql")
	series_sql = (f"{DATA_DIR}{os.path.sep}series.sql")
	music_sql = (f"{DATA_DIR}{os.path.sep}music.sql")
	if os.path.exists(movies_sql):
		new_sql = (f"{movies_sql}.{ts}.backup.sql")
		com = (f"mv '{movies_sql}' '{new_sql}'")
		ret = run_shell(com)
		if ret is not True:
			log(f"Error: {ret}", 'error')
			input()
	if os.path.exists(series_sql):
		new_sql = (f"{series_sql}.{ts}.backup.sql")
		com = (f"mv '{series_sql}' '{new_sql}'")
		ret = run_shell(com)
		if ret is not True:
			log(f"Error: {ret}", 'error')
			input()
	if os.path.exists(music_sql):
		new_sql = (f"{music_sql}.{ts}.backup.sql")
		com = (f"mv '{music_sql}' '{new_sql}'")
		ret = run_shell(com)
		if ret is not True:
			log(f"Error: {ret}", 'error')
			input()
	log("dumping movies..", 'info')
	com = (f"cd '{DATA_DIR}'; sqlite3 nplayer.db '.dump movies' > movies.sql")
	ret = run_shell(com)
	if ret is not True:
		log(f"Error: {ret}", 'error')
		input()
	log("dumping series...", 'info')
	com = (f"cd '{DATA_DIR}'; sqlite3 nplayer.db '.dump series' > series.sql")
	ret = run_shell(com)
	if ret is not True:
		log(f"Error: {ret}", 'error')
		input()
	log("dumping music...", 'info')
	com = (f"cd '{DATA_DIR}'; sqlite3 nplayer.db '.dump music' > music.sql")
	ret = run_shell(com)
	if ret is not True:
		log(f"Error: {ret}", 'error')
		input()

def remove_items(_list, table):
	log(f"removing from {table}...", 'info')
	pos = 0
	dbfile = (f"{DATA_DIR}{os.path.sep}nplayer.db")
	for _id in _list:
		pos += 1
		log(f"Removing id: {_id}. Progress: {pos}/{len(_list)}", 'info')
		com = (f"sqlite3 '{dbfile}' 'delete from {table} where id = {_id};'")
		ret = subprocess.check_output(com, shell=True).decode()
		if ret is not True and ret != '':
			log(f"cleandb.py: Error encountered in removal. ID: {_id}, Data: '{ret}'", 'error')
	return True

def clean_movies():
	log("Scanning movies for duplicates..", 'info')
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
			log(f"Duplicate:{title}", 'info')
	log(f"Found {len(trash)} duplicate entries.", 'info')
	remove_items(trash, 'movies')
	log("Done!", 'info')

def clean_series():
	log("Scanning series for duplicates..", 'info')
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
			log(f"Duplicate:{string}:{series_name}:{season}:{episode_number}", 'info')
	log(f"Found {len(trash)} duplicate entries.", 'info')
	remove_items(trash, 'series')
	log("Done!", 'info')

def clean_music():
	log("Scanning music for duplicates..", 'info')
	com = (f"cd '/home/monkey/.np'; sqlite3 nplayer.db 'select artist,title,id from music order by artist,title;'")
	_list = subprocess.check_output(com, shell=True).decode().strip().split('\n')
	keep = []
	trash = []
	for item in _list:
		try:
			chunks = item.split('|')
			artist = chunks[0]
			title = chunks[1]
			_id = chunks[2]
			string = (f"{artist}:{title}")
			if string not in keep:
				keep.append(string)
			elif string in keep:
				trash.append(_id)
				log(f"Duplicate:{string}", 'info')
		except:
			pass
	log(f"Found {len(trash)} duplicate entries (out of {len(_list)})...", 'info')
	remove_items(trash, 'music')
	log("Done!", 'info')

def run(opt="all"):
	backup_db()
	if opt == "all":
		log("Checking entire database for duplicates...", 'info')
		clean_movies()
		clean_series()
		clean_music()
		return True
	elif opt == 'music':
		log("Checking music database for duplicates...", 'info')
		clean_music()
		return True
	elif opt == 'series':
		log("Checking series database for duplicates...", 'info')
		clean_series()
		return True
	elif opt == 'movies':
		log("Checking movies database for duplicates...", 'info')
		clean_movies()
		return True
	else:
		log("Unrecognized option! Whoopsie doodles...", 'error')
		return False


if __name__ == "__main__":
	run()
