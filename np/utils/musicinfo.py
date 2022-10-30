from np.utils.id3 import tag
import requests
from bs4 import BeautifulSoup
import pickle
import os
import subprocess

id3 = tag()
songs = {}
def read_fp(filepath):
	return subprocess.check_output(f"fpcalc \"{filepath}\"", shell=True).decode().strip()

def read_tag(filepath):
	title = None
	artist = None
	try:
		tag = id3.read(filepath)
		title = tag.title
		artist = tag.artist
	except Exception as e:
		print(f"Couldn't get tag data: {e}")
	return title, artist

def store_data(path='/var/storage/Music/Old'):
	os.chdir(path)
	files = next(os.walk(path))[2]
	ct = len(files)
	pos = 0
	for filepath in files:
		filepath = os.path.abspath(filepath)
		pos += 1
		print(f"Progress: {pos}/{ct}...")
		if '.mp3' in filepath:
			title, artist = read_tag(filepath)
			if title is None or artist is None:
				print("No tag data! Guessing by file name...")
				fname = os.path.basename(filepath)
				chunks = fname.split('-')
				if len(chunks) == 3:
					artist = fname.split('-')[0].strip()
					title = fname.split('-')[1].strip()
				else:
					print("Un-normalized name encountered!", fname)
					if len(chunks) == 2:
						title = fname.split('-')[0]
						yn = input(f"Use title {title}?")
						if yn != 'y':
							title = input("Enter title: ")
						artist = input("Enter artist name: ")
					else:
						title = input("Enter title: ")
						artist = input("Enter artist name: ")
			album = find_album(artist, title)
			fp = read_fp(filepath)
			songs[filepath] = {}
			songs[filepath]['artist'] = artist
			songs[filepath]['title'] = title
			songs[filepath]['fp'] = fp
			songs[filepath]['album'] = album

	write_data(songs, path)
	return songs


def find_album(artist, title):
	query = f"{artist} {title} album"
	url = f"https://www.google.com/search?q={query}"
	r = requests.get(url)
	if r.status_code == 200:
		sr = BeautifulSoup(r.text, "html.parser")
		album = sr.find("div", class_='BNeawe').text
		return album
	else:
		log(f"Error: Bad status code! {r.status_code}", 'error')
		return None


def write_data(songs, path='/var/storage/Music/Old'):
	id3_datfile = os.path.join(path, 'id3_datfile.dat')
	with open(id3_datfile, "wb") as f:
		pickle.dump(songs, f)
		f.close()
	return


def read_data(path='/var/storage/Music/Old'):
	id3_datfile = os.path.join(path, 'id3_datfile.dat')
	with open(id3_datfile, "rb") as f:
		songs = pickle.load(f)
		f.close()
	return songs


def rename_file(filepath):
	filepath = filepath.replace("'", "\'")
	tag = id3.read(filepath)
	fdir = os.path.dirname(filepath)
	fname = os.path.basename(filepath)
	ext = os.path.splitext(filepath)[1]
	newname = f"{tag.artist} - {tag.title}{ext}"
	newname = newname.replace("'", '')
	newfilepath = os.path.join(fdir, newname)
	print(f"Moving: old={filepath}, new={newfilepath}")
	#input("Press enter to migrate...")
	try:
		ret = subprocess.check_output(f"mv \"{filepath}\" \"{newfilepath}\"", shell=True).decode().strip()
		if ret != '':
			print(f"Error moving file: {ret}!")
			return False
		else:
			print("Ok!")
			return True
	except Exception as e:
		print(f"Error moving file: {e}!")
		return False


def update_tag(filepath, title=None, artist=None, album=None, guess=True):
	fname = os.path.basename(filepath)
	tag = id3.read(filepath)
	tag.comment = 'Tag created by python_np (tag_editor)'
	tag.track = 0
	if artist is None or artist == '':
		if tag.artist == '':
			current_artist = fname.split('-')[0].strip()
			if guess is False:
				newartist = input(f"Enter artist (Current: {current_artist}), empty to keep current: ")
			else:
				newartist = ''
			if newartist == '':
				tag.artist = current_artist
			else:
				tag.artist = newartist
	else:
		tag.artist = artist
	if title is None or title == '':
		if tag.title == '':
			current_title = fname.split('-')[1].strip()
			if '(' in current_title:
				current_title = current_title.split('(')[0].strip()
			elif '[' in current_title:
				current_title = current_title.split('[')[0].strip()
			if guess is False:
				newtitle = input(f"Enter title (Current: {current_title}), empty to keep current: ")
			else:
				newtitle = ''
			if newtitle == '':
				tag.title = current_title
			else:
				tag.title = newtitle
	else:
		tag.title = title
	if album is None or album == '':
		if tag.album == '':
			tag.album = find_album(tag.artist, tag.title)
	else:
		tag.album = album
	tag.save()
	print("Tag updated!")


def test_file(filepath, path=None):
	if path is None:
		path='/var/storage/Music/Old'
	if "'" in filepath or '"' in filepath:
		print("Found quote in filename! renaming...")
		filepath = filepath.replace("'", '\'')
		newpath = filepath.replace("'", "")
		ret = subprocess.check_output(f"mv \"{filepath}\" \"{newpath}\"", shell=True).decode().strip()
		if ret != '':
			print(f"Couldn't rename! {ret}")
			input("Press enter to abort...")
			exit()
		else:
			filepath = newpath
	print("Testing file: ", filepath)
	songs = read_data()
	fps = []
	files = []
	for testpath in songs.keys():
		fps.append(songs[testpath]['fp'])
		files.append(testpath)
	fp = read_fp(filepath)
	if fp in fps:
		migrate = False
		idx = fps.index(fp)
		match_path = files[idx]
		match_data = songs[match_path]
		matched_filepath = files[idx]
		print(f"found match! Matched file:{matched_filepath}, title:{match_data['title']}, artist:{match_data['artist']}, album:{match_data['album']}")
		tag = id3.read(filepath)
		if tag.artist == '' or tag.album == '' or tag.title == '':
			print("Blank tag found! Updating...")
			update_tag(filepath)
		else:
			print(f"Found previous tag data: Artist:{tag.artist}, Album:{tag.album}, Title:{tag.title}, Filepath:{tag.filepath}!")
			if match_data['artist'] != tag.artist:
				artist = match_data['artist']
				migrate = True
			else:
				artist = tag.artist
			if match_data['title'] != tag.title:
				title = match_data['title']
				migrate = True
			else:
				title = tag.title
			if match_data['album'] != tag.album:
				migrate = True
				album = match_data['album']
			else:
				album = tag.album
			update_tag(filepath, artist=artist, title=title, album=album)
		fdir = os.path.dirname(filepath)
		ext = os.path.splitext(filepath)[1]
		testname = f"{tag.artist} - {tag.title}{ext}"
		tpath = os.path.join(fdir, testname)
		if filepath != tpath or migrate is True:
			print("renaming file with new tag info...")
			ret = rename_file(filepath)
			if ret:
				print("Done!")
			else:
				print("Migrate failed.")
		else:
			print("Path from tag data and current path match! No rename necessary.")
			pass
			
	else:
		tag = id3.read(filepath)
		if tag.title == '' and tag.artist == '' and tag.album == '':
			print("No tag data! Guessing info from file name...")
			fname = os.path.basename(filepath)
			chunks = fname.split('-')
			if len(chunks) >= 3:
				artist = fname.split('-')[0].strip()
				title = fname.split('-')[1].strip()
			else:
				print("Un-normalized name encountered!", fname)
				tag.artist = input("Enter artist name: ")
				tag.title = input("Enter title: ")
			if tag.album == '':
				tag.album = find_album(tag.artist, tag.title)
		print(f"Title:{tag.title}, Artist:{tag.artist}, Album:{tag.album}, Filepath:{filepath}")
		#input("Press enter to update tag and add to datfile...")
		update_tag(filepath, title=tag.title, artist=tag.artist, album=tag.album)
		print("updating dat file...")
		songs[filepath] = {}
		songs[filepath]['artist'] = tag.artist
		songs[filepath]['album'] = tag.album
		songs[filepath]['title'] = tag.title
		songs[filepath]['fp'] = fp
		write_data(songs, path)
		print("Renaming file...")
		ret = rename_file(filepath)
		if ret:
			print("Done!")
		else:
			print("Migrate failed.")
		

if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser(description='MP3 id3 tag data data indexer')
	parser.add_argument('-f','--function', help="Function to run. Defaults to 'store'. Available options are 'store', 'test_file', and 'test_dir'.", default='store')
	parser.add_argument('-d','--directory', help="Directory containing music files. Also where dat file will be stored.", default=None)
	parser.add_argument('-t','--test-file', help="Specify a test file to check against the fingerprint database. Overrides -f.")
	parser.add_argument('-T','--test-dir', help="Specify a directory of files to check against the fingerprint database. Overrides -f")
	args = parser.parse_args()
	if args.directory is None:
		args.directory = os.path.join(os.path.expanduser("~"), 'Music')
	if args.test_file is not None:
		print("test file provided, overriding function to 'test'!")
		args.function = 'test_file'
		target = args.test_file
	elif args.test_dir is not None:
		args.function = 'test_dir'
		target = args.test_dir
	if args.function == 'store':
		id3_datfile = os.path.join(args.directory, 'id3_datfile.dat')
		if os.path.exists(id3_datfile):
			print(f"Dat file exists! If you want a new database, delete first! ({id3_datfile})")
			songs = read_data(args.directory)
		else:
			songs = store_data(args.directory)
		print(songs)
	elif args.function == 'test_file':
		if target is None:
			print("No test file provided! exiting...")
			exit()
		else:
			print(test_file(target, args.directory))
	elif args.function == 'test_dir':
		os.chdir(target)
		files = next(os.walk(target))[2]
		ct = len(files)
		pos = 0
		for filepath in files:
			pos += 1
			print(f"Progress: {pos}/{ct}")
			filepath = os.path.abspath(filepath)
			print(test_file(filepath, args.directory))
