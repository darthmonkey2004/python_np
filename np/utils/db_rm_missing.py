import os
import subprocess

def sqlite3(query):
	dbfile = os.path.join(os.path.expanduser("~"), '.np', 'nplayer.db')
	com = f"sqlite3 \"{dbfile}\" \"{query}\""
	try:
		ret = subprocess.check_output(com, shell=True).decode().strip()
		if "\n" in ret:
			ret = ret.split("\n")
		return ret
	except Exception as e:
		print("Error in sqlite3: {e}", 'error')
		return None


def get_files():
	d = {}
	movies = sqlite3("select id,filepath from movies;")
	for movie in movies:
		_id, filepath = movie.split('|')
		d[_id] = {}
		d[_id]['filepath'] = filepath
		d[_id]['type'] = movies
		
	series = sqlite3("select id,filepath from series;")
	for item in series:
		_id, filepath = item.split('|')
		d[_id] = {}
		d[_id]['filepath'] = filepath
		d[_id]['type'] = series
	music = sqlite3("select id,filepath from music;")
	for item in music:
		_id, filepath = item.split('|')
		d[_id] = {}
		d[_id]['filepath'] = filepath
		d[_id]['type'] = music
	return d


def log_deletions(filepath):
	with open("db_deletions.txt", 'w') as f:
		f.write(filepath)
		f.close()


def ck_exists(filepath):
	if os.path.exists(filepath):
		return True
	else:
		return False


def delete(_id, _type):
	ret = sqlite3(f"delete from {_type} where id = {_id};")

yesses = 0
file_dict = get_files()
ct = len(file_dict.keys())
pos = 0
skip_confirmation = False
for _id in file_dict.keys():
	pos += 1
	filepath = file_dict[_id]['filepath']
	_type = file_dict[_id]['type']
	print(f"Progress: {pos}/{ct}: Filepath=\"{filepath}\"")
	if not ck_exists(filepath):
		print(f"Found missing file: {filepath}!")
		if not skip_confirmation:
			input("Press enter to remove and continue...")
			ret = delete(_id, _type)
			if ret is not None and ret != '':
				print(f"Error removing: {ret}!")
			else:
				log_deletions(filepath)
			yesses += 1
			if yesses == 5:
				yn = input("Skip confirmation from now on?")
				if yn == "y":
					skip_confirmation = True
					print("Skipping..")
				else:
					print("Playing it safe...")
					skip_confirmation = False
		else:
			ret = delete(_id, _type)
			if ret is not None and ret != '':
				print(f"Delete command returned data: {ret}", 'warning')
			else:
				log_deletions(filepath)
print("Finished!")
exit()
