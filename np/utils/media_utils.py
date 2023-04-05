#from np.utils.pbdl.dl_missing import *
from helper_utils.sql import *
from helper_utils.log import logger
from helper_utils.filesystem import filesystem
import os, subprocess, pickle


fs = filesystem()
path = os.path.join(os.path.expanduser("~"), '.np')
dbfile = os.path.join(path, 'nplayer.db')
logfile = os.path.join(path, 'nplayer.log')
logger = logger(logfile=logfile, verbose=True)
log = logger.log_msg
sql = sql(dbfile)

def get_mean_volume(filepath, target=-32.1):
	com = f"ffmpeg -i \"{filepath}\" -af volumedetect -vn -sn -dn -f null - 2>&1"
	try:
		data = subprocess.check_output(com, shell=True).decode().strip().splitlines()
	except Exception as e:
		log(f"Error detecting volume: {e}, filepath={filepath}", 'error')
		return target, 0
	for line in data:
		if 'mean_volume:' in line:
			mean = round(float(line.split('mean_volume: ')[1].split(' ')[0]), 1)
			#break
		elif 'max_volume' in line:
			maxvol = round(float(line.split('max_volume: ')[1].split(' ')[0]), 1)
	return mean, maxvol

def _normalize_action(volume, filepath, outpath):
	com = f"ffmpeg -y -i \"{filepath}\" -filter:a \"volume={volume}dB\" \"{outpath}\" -f null - 2>&1"
	subprocess.check_output(com, shell=True).decode().strip()

def get_mean_volumes(files=None):
	d = {}
	if files is None:
		files = sql.query(f"select filepath from series;")
	ct = len(files)
	pos = 0
	for filepath in files:
		pos += 1
		d[filepath] = {}
		d[filepath]['mean'], d[filepath]['max'] = get_mean_volume(filepath)
		log(f"get_mean_volumes():Progress: {pos} of {ct} ({d[filepath]}), file:{filepath}", 'info')
	save_normalize_data(d)
	return d

def _normalize(d=None, test_volume=False):
	if d is None:
		d = filter_normalize_results(load_normalize_data())
	pos = 0
	ct = len(d)
	target = -32.1
	for filepath in d.keys():
		pos += 1
		log(f"Progress:{pos}/{ct} (file:{filepath})...", 'info')
		dir = os.path.dirname(filepath)
		path = os.path.dirname(filepath)
		fname = os.path.basename(filepath)
		fname = os.path.splitext(fname)[0]
		ext = os.path.splitext(filepath)[1].split('.')[1]
		normpath = os.path.join(path, f"{fname}.normalized.{ext}")
		out = os.path.join(dir, f"{fname}.normalized.{ext}")
		com = f"ffmpeg -i \"{filepath}\" -af volumedetect -vn -sn -dn -f null - 2>&1"
		cont = False
		if test_volume:
			try:
				mean = get_mean_volume(filepath)
				volume = round(target - float(mean), 1)
				if volume >= -0.5 and volume <= 0.5:
					log(f"already normalized (mean:{mean}, target:{target})! Skipping file ({filepath})...", 'info')
					cont = False
				else:
					log(f"needs normalization! (mean:{mean}, target:{target}, file:{filepath}", 'info')
					cont = True
			except Exception as e:
				txt = f"Error detecting volume: {e} (file:{filepath})"
				log(txt, 'error')
				cont = False
		else:
			cont = True
			volume = d[filepath]
		if cont:
			data = _normalize_action(volume, filepath, out)
			if not os.path.exists(normpath):
				txt = "Error! new file not at location ({normpath)! Aborting..."
				log(txt, 'error')
				break
			else:
				log(f"transcoding successful: {normpath}", 'info')
				if os.path.exists(filepath):
					fs.rm(filepath)
				else:
					txt = f"weirdly enough, file is missing? ({filepath})", 'error'
					log(txt, 'error')
					raise Exception(txt)
				log(f"found:{normpath}! Moving...", 'info')
				fs.mv(normpath, filepath)

def filter_normalize_results(d, volrange=(-1, 1)):
	todo = {}
	for filepath in d.keys():
		mean = float(d[filepath])
		target = -32.1
		dist = round(mean - target, 1)
		if dist < volrange[0] or dist >= volrange[1]:
			print("target:", target, "mean:", mean, "distance:", dist)
			todo[filepath] = mean
	return todo

def save_normalize_data(d, savepath=os.path.join(os.path.expanduser("~"), '.np', 'normalize_targets.dat')):
	with open(savepath, 'wb') as f:
		pickle.dump(d, f)
		f.close()

def load_normalize_data(savepath=os.path.join(os.path.expanduser("~"), '.np', 'normalize_targets.dat')):
	with open(savepath, 'rb') as f:
		data = pickle.load(f)
		f.close()
	return data

def normalize(savepath=os.path.join(os.path.expanduser("~"), '.np', 'normalize_targets.dat'), test_volume=False):
	if os.path.exists(savepath):
		d = load_normalize_data(savepath)
		log(f"normalize data loaded! (found {len(d)} files)", 'info')
	else:
		log(f"normalization data not found. Scanning...", 'warning')
		d = get_mean_volumes()
	files = filter_normalize_results(d)
	_normalize(files, test_volume=test_volume)

def db_get_missing_items(tables=None, remove=False):
	missing = []
	if tables is None:
		tables = ['series', 'movies', 'music']
	else:
		if type(tables) == str:
			tables = [tables]
		elif type(tables) == tuple:
			tables = list(tables)
	for table in tables:
		files = sql.query(f"select filepath from {table};")
		for filepath in files:
			if os.path.exists(filepath):
				log(f"media_utils.db_file_exists():File ok - {filepath}!", 'info')
			else:
				log(f"media_utils.db_file_exists():File missing! {filepath}", 'warning')
				missing.append(filepath)
	if remove:
		log(f"media_utils.db_file_exsts():Removing missing entries... (remove=True)", 'info')
		for filepath in missing:
			sql.send(f"delete from {table} where filepath = '{filepath}';")
			log(f"media_utils.db_file_exists(): removed entry from database: {filepath}", 'info')
	else:
		return missing



def get_all_files(path, pattern=None):
	if pattern is None:
		com = f"find \"{path}\" -name \"*.*\""
	else:
		com = f"find \"{path}\" -name \"{pattern}\""
	return subprocess.check_output(com, shell=True).decode().strip().splitlines()
